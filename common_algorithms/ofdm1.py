import sys
from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from defs import write_pipe, log
import numpy as np
import scipy.signal as sig
import matplotlib.pyplot as plt
import time

BYTES_PER_SYMBOL = 480
PILOT_INTERVAL = 16
SYMBOL_LENGTH = 1024
GUARD_LENGTH = 256
ISI_LENGTH = SYMBOL_LENGTH+GUARD_LENGTH
SAMPLES_PER_SYMBOL = (SYMBOL_LENGTH+GUARD_LENGTH)*3
SAMPLES_PER_GUARD = GUARD_LENGTH*3
FS = 48000
MLS_FREQ = 21000 

def linregress(y, x0=0, dx=1):
    """
    Performs a linear regression on y, where the abscissa at y[i] is x0+dx*i
    Returns (slope, intercept).
    If y is relatively small this can be dozens of times faster than
    scipy.stats.linregress
    Taken from https://www.embeddedrelated.com/showarticle/1163.php
    """
    m = len(y)
    w = 1.0 / m
    q = 12.0 / (m**3 - m)
    c0 = 0.0
    c1 = 0.0
    ibar = (m-1)/2.0
    c0 = np.sum(y)*w
    c1 = q * np.sum( y * (np.arange(len(y)) - ibar) )
    slope = c1/dx
    ofs = c0 - slope*x0 - c1*ibar
    return slope, ofs

def quartet_to_qam(quartet: int) -> complex:
    out = 0.0+0.0j
    match (quartet & 0b1100)>>2:
        case 0b00: out += -1.5
        case 0b01: out += -0.5
        case 0b11: out += 0.5
        case 0b10: out += 1.5
    match (quartet & 0b0011):
        case 0b00: out += 1.5j
        case 0b01: out += 0.5j
        case 0b11: out += -0.5j
        case 0b10: out += -1.5j
    return out

def qam_to_quartet(qam: complex) -> int:
    out = 0
    if qam.real < -1:
        pass
    elif qam.real < 0:
        out |= 0b0100
    elif qam.real < 1:
        out |= 0b1100
    else:
        out |= 0b1000
    if qam.imag < -1:
        out |= 0b0010
    elif qam.imag < 0:
        out |= 0b0011
    elif qam.imag < 1:
        out |= 0b0001
    else:
        out |= 0b0000
    return out

def octet_to_qam(byte: int) -> list[complex]:
    symbol1 = quartet_to_qam((byte & 0b1111_0000)>>4)
    symbol2 = quartet_to_qam(byte & 0b0000_1111)
    return [symbol1, symbol2]

def bytes_to_qam(data: bytes) -> list[complex]:
    return sum([octet_to_qam(byte) for byte in data], [])

def qam_to_bytes(signal: np.ndarray|list[complex]) -> bytes:
    assert len(signal)%2 == 0
    out = []
    for symbol1, symbol2 in zip(signal[::2], signal[1::2]):
        out.append(qam_to_quartet(symbol1)<<4 | qam_to_quartet(symbol2))
    return bytes(out)

assert all([x == qam_to_bytes(octet_to_qam(x))[0] for x in range(256)])

def invHilbert(cData: np.ndarray) -> np.ndarray[tuple[int], np.dtype[np.float32]]:
    cFreqData = np.fft.fft(cData)[:(len(cData)//2+1)]
    data = 0.5*np.fft.irfft(cFreqData)
    return np.asarray(data, dtype=np.float32)


mls = sig.max_len_seq(8)[0]
def generate_mls_signal(length=3*ISI_LENGTH, mls_length=ISI_LENGTH, freq=MLS_FREQ, energy=3) -> list[complex]:
    # We need to stretch mls to be approximately the same length as default_length
    stretch_factor = (length-1)//len(mls)
    stretched = np.repeat(mls, stretch_factor)
    code_seq = np.append(stretched, [stretched[-1]]*(length-len(stretched)))
    t = np.linspace(0, (length-1)/FS, length)
    sig1 = energy/len(t)*np.exp(2*np.pi*1j*freq*t)
    sig2 = energy/len(t)*np.exp(2*np.pi*1j*freq*t+np.pi/2)
    return sig1*code_seq + sig2*(1-code_seq) # type: ignore


def add_every_nth(arr, new_item, n:int):
    n -= 1
    return sum([arr[i:i+n]+[new_item] for i in range(0, len(arr), n)], [])


def remove_every_nth(arr, n: int):
    return sum([list(arr[i:i+n-1]) for i in range(0, len(arr), n)], [])


def generate_segment(data: bytes, add_mls=True):
    """
    Given some bytes, returns a real waveform (not at baseband) representing
    the provided signal.

    data: A bytes object of length BYTES_PER_SYMBOL
    """
    assert len(data) == BYTES_PER_SYMBOL
    data = scramble(data)
    # data = add_every_nth(data, b'\0', PILOT_INTERVAL)
    qam_symbols = bytes_to_qam(data)
    qam_symbols = add_every_nth(qam_symbols, -1.5+1.5j, PILOT_INTERVAL)
    ifft = np.fft.ifft(qam_symbols)
    resampled = sig.resample(ifft, len(ifft)*3)
    t = np.linspace(0, (len(resampled)-1)/FS, len(resampled))
    shifted = resampled * np.exp(2*np.pi*1j*(FS//6+500)*t)
    with_guard = np.append(shifted[-GUARD_LENGTH*3:], shifted)
    if add_mls:
        with_guard += generate_mls_signal()
    return invHilbert(with_guard)/8


def decode_segment(segment: np.ndarray) -> bytes:
    """
    segment: A numeric array, with
    SYMBOL_LENGTH*3 <= len(segment) <= (SYMBOL_LENGTH+GUARD_LENGTH)*3
    If the length is less than (SYMBOL_LENGTH+GUARD_LENGTH)*3, that should be because
    the front of the guard is missing.
    """
    assert SYMBOL_LENGTH*3 <= len(segment) <= (SYMBOL_LENGTH+GUARD_LENGTH)*3
    analytic = sig.hilbert(segment)
    without_guard = analytic[-3*SYMBOL_LENGTH:]
    t = np.linspace(0, (len(without_guard)-1)/FS, len(without_guard))
    baseband = without_guard * np.exp(-2*np.pi*1j*(FS//6+500)*t)
    downsampled = sig.resample(baseband, len(baseband)//3)
    qam_symbols = np.fft.fft(downsampled)
    # We compensate for any phase changes caused by getting the time-offset wrong.
    pilots = qam_symbols[PILOT_INTERVAL-1::PILOT_INTERVAL]
    phases = np.unwrap(np.angle(pilots), .3)
    slope, offset = linregress(phases)
    time_offset = slope/(500 * np.pi)
    # log(f"Estimated old offset: {time_offset*1000} ms ({time_offset*48000} samples @ 48 KHz)")
    # time_offset = np.mean(np.ediff1d(phases))/(500*np.pi)
    # log(f"Estimated offset: {time_offset*1000} ({time_offset*48000})")
    time_offset = np.median(np.ediff1d(phases))/(500*np.pi)
    # log(f"Estimated new offset: {time_offset*1000} ({time_offset*48000})")
    f = np.linspace(0, 16000, len(qam_symbols))
    qam_symbols *= np.exp(-2*np.pi*1j*time_offset*f)
    pilots = qam_symbols[PILOT_INTERVAL-1::PILOT_INTERVAL]
    qam_symbols *= (-1.5+1.5j)/np.mean(pilots)
    # plot_constellation(qam_symbols)
    pilots_removed = remove_every_nth(qam_symbols, PILOT_INTERVAL)
    return unscramble(qam_to_bytes(pilots_removed))

def plot_complex(*args, name=""):
    if len(args) == 1:
        data = args[0]
        plt.plot(np.real(data), label="real")
        plt.plot(np.imag(data), label="imag")
    elif len(args) == 2:
        x, y = args[0], args[1]
        plt.plot(x, np.real(y), label="real")
        plt.plot(x, np.imag(y), label="imag")
    plt.legend()
    plt.title(name)
    plt.show()


def plot_constellation(data, qam=16):
    plt.scatter(data.real, data.imag)
    plt.scatter(*np.meshgrid([-1.5, -.5, .5, 1.5], [-1.5, -.5, .5, 1.5])) # type:ignore
    plt.show()


def bytes2binstr(b, n=None):
    s = ''.join(f'{x:08b}' for x in b)
    return s if n is None else s[:n + n // 8 + (0 if n % 8 else -1)]

def binstr2bytes(s: str) -> bytes:
    out = []
    for i in range(len(s)//8):
        byte_str = s[i*8:(i+1)*8]
        out.append(int(byte_str, 2))
    return bytes(out)

def scramble(data: bytes) -> bytes:
    x = np.array(list(bytes2binstr(data))).reshape(64, 60, order='F')
    bits_scrambled = ''.join(np.hstack(x)) # type: ignore
    return binstr2bytes(bits_scrambled)

def unscramble(data: bytes) -> bytes:
    x = np.array(list(bytes2binstr(data))).reshape(64, 60)
    bits = ''.join(np.hstack(x.T)) # type: ignore
    return binstr2bytes(bits)

def synchronize(signal: np.ndarray):
    """
    Signal: One full frame length
    Empirically, this has a minimum SNR somewhere between 30 and 35 dB
    Returns the start index of the first full frame
    """
    mls_signal = generate_mls_signal(3*ISI_LENGTH, MLS_FREQ)
    filter = sig.butter(4, (MLS_FREQ-1000, MLS_FREQ+1000), btype="bandpass", fs=FS, output="sos")
    filtered = sig.sosfiltfilt(filter, signal)
    corr = np.abs(sig.correlate(mls_signal, filtered))
    filter2 = sig.butter(4, 0.01, output='sos')
    corr -= sig.sosfiltfilt(filter2, corr)
    lags = sig.correlation_lags(len(mls_signal), len(signal))
    argmax = np.argmax(corr)
    # plt.plot(corr)
    # plt.show()
    if corr[argmax]/np.std(corr) > 4:
        return (-lags[argmax])%(3*ISI_LENGTH)
    return None

if __name__ == "__main__":
    data = bytes(list(np.random.randint(0, 256, 256+255)))[:BYTES_PER_SYMBOL]
    data = bytes([0]*BYTES_PER_SYMBOL)
    start = time.time()
    signal = generate_segment(data, add_mls=True)
    # log(signal[:20]*1000)
    # log(signal[:20]*1000)
    # decoded = decode_segment(signal)
    # end = time.time()
    # log("Took %f ms" % ((end-start)*1000))
    # log(len(data))
    # log(len(decoded))
    # assert data[:BYTES_PER_SYMBOL] == decoded[:BYTES_PER_SYMBOL]
    data2 = bytes(list(np.random.randint(0, 256, 256+255)))[:BYTES_PER_SYMBOL]
    data3 = bytes(list(np.random.randint(0, 256, 256+255)))[:BYTES_PER_SYMBOL]
    data4 = bytes(list(np.random.randint(0, 256, 256+255)))[:BYTES_PER_SYMBOL]
    signal2 = generate_segment(data2, True)
    signal3 = generate_segment(data3, True)
    signal4 = generate_segment(data4, True)
    true_idx = 4
    incoming_signal = np.append(np.append(signal2, signal3), signal4)[true_idx:]
    rms_amplitude = np.sqrt(np.mean(np.abs(incoming_signal)**2))
    log(f"signal rmse: {rms_amplitude}")
    snr = 350
    log("This has a poor sensitivity to noise. Consider changing to 4-QAM (4-QPSK?)")
    log(f"{snr=} dB")
    noise_multiplier = np.sqrt(10**(-snr/10)*rms_amplitude)
    noise = np.random.normal(0, noise_multiplier, incoming_signal.shape)
    noise_power = np.mean(np.abs(noise)**2)
    log(f"noise power: {noise_power}")
    # incoming_signal += noise
    idx = synchronize(incoming_signal[:3*ISI_LENGTH])
    log(f"est idx: {idx}")
    log(f"offset error: {idx-(3840-true_idx)}") # type:ignore
    # I'm getting slammed by the time shifting property. This adds a phase
    # difference that's linear with time. Use the 32 added 0 bytes to find,
    # remove this phase difference. Also need to 
    if idx is not None:
        decoded2 = decode_segment(incoming_signal[idx:idx+3*ISI_LENGTH])
        log(f"true:   {bytes2binstr(data2[:10])} ... {bytes2binstr(data2[-10:])}")
        log(f"true:   {bytes2binstr(data3[:10])} ... {bytes2binstr(data3[-10:])}")
        log(f"result: {bytes2binstr(decoded2[:10])} ... {bytes2binstr(decoded2[-10:])}")
    else:
        print("idx is None")
# length = len(signal)
# signal_offset = list(generate_segment(data)[123]) + [0.0 + 0.0j]*(456)
# signal_offset = np.array(signal_offset[-length:], dtype=np.complex64)
