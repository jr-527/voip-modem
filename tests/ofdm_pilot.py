import sys
from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from defs import write_pipe, log
import numpy as np
import scipy.signal as sig
import matplotlib.pyplot as plt
import time

SYMBOL_LENGTH = 1024
GUARD_LENGTH = 256
ISI_LENGTH = SYMBOL_LENGTH+GUARD_LENGTH
FS = 48000
MLS_FREQ = 21000 


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

# I have no idea who decided that
# def foo() -> np.ndarray[tuple[int], np.dtype[np.float32]]:
# is better than
# float[] foo()
def invHilbert(cData: np.ndarray) -> np.ndarray[tuple[int], np.dtype[np.float32]]:
    cFreqData = np.fft.fft(cData)[:(len(cData)//2+1)]
    data = 0.5*np.fft.irfft(cFreqData)
    return np.asarray(data, dtype=np.float32)


mls = sig.max_len_seq(8)[0]
def generate_mls_signal(length=3*ISI_LENGTH, mls_length=ISI_LENGTH, freq=MLS_FREQ, energy=3) -> list[complex]:
    # We need to stretch mls to be approximately the same length as default_length
    stretch_factor = length//len(mls)
    stretched = np.repeat(mls, stretch_factor)
    code_seq = np.append(stretched, [stretched[-1]]*(length-len(stretched)))
    t = np.linspace(0, length/FS, length)
    sig1 = energy/len(t)*np.exp(2*np.pi*1j*freq*t)
    sig2 = energy/len(t)*np.exp(2*np.pi*1j*freq*t+np.pi/2)
    return sig1*code_seq + sig2*(1-code_seq) # type: ignore


def generate_segment(data: bytes, add_mls=False):
    """
    Given some bytes, returns a complex waveform (not at baseband) representing
    the provided signal.

    data: A bytes object of length 512
    """
    assert len(data) == SYMBOL_LENGTH//2
    data = data[:-2] + bytes([0, 0])
    qam_symbols = bytes_to_qam(data)
    ifft = np.fft.ifft(qam_symbols)
    resampled = sig.resample(ifft, len(ifft)*3)
    t = np.linspace(0, len(resampled)/FS, len(resampled))
    shifted = resampled * np.exp(2*np.pi*1j*(FS//6+500)*t)
    with_guard = np.append(shifted[-GUARD_LENGTH*3:], shifted)
    if add_mls:
        with_guard += generate_mls_signal()
    return invHilbert(with_guard)


def decode_segment(segment: np.ndarray) -> bytes:
    assert len(segment) == (SYMBOL_LENGTH+GUARD_LENGTH)*3
    analytic = sig.hilbert(segment)
    without_guard = analytic[GUARD_LENGTH*3:]
    t = np.linspace(0, len(without_guard)/FS, len(without_guard))
    baseband = without_guard * np.exp(-2*np.pi*1j*(FS//6+500)*t)
    downsampled = sig.resample(baseband, len(baseband)//3)
    qam_symbols = np.fft.fft(downsampled)
    qam_symbols *= (-1.5+1.5j)/qam_symbols[-1]
    return qam_to_bytes(qam_symbols)

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

def synchronize(signal: np.ndarray):
    # Signal: One full frame length
    # Returns the start index of the first full frame
    mls_signal = generate_mls_signal(3*ISI_LENGTH, MLS_FREQ)
    filter = sig.butter(4, (MLS_FREQ-1000, MLS_FREQ+1000), btype="bandpass", fs=FS, output="sos")
    filtered = sig.sosfiltfilt(filter, signal)
    corr = sig.correlate(mls_signal, filtered)
    lags = sig.correlation_lags(len(mls_signal), len(signal))
    return (-lags[np.argmax(np.abs(corr))])%(3*ISI_LENGTH)

if __name__ == "__main__":
    data = bytes(list(range(256))+list(range(256)))
    start = time.time()
    signal = generate_segment(data, add_mls=True)
    decoded = decode_segment(signal)
    end = time.time()
    log("Took %f ms" % ((end-start)*1000))
    assert data[:510] == decoded[:510]
    data2 = bytes([5,100,200,50]*128)
    data3 = bytes([0,255]*256)
    data4 = bytes([10,20,30,40,50,60,70,80]*64)
    signal2 = generate_segment(data2, True)
    signal3 = generate_segment(data3, True)
    signal4 = generate_segment(data4, True)
    incoming_signal = np.append(np.append(signal2, signal3), signal4)[700:]
    idx = synchronize(incoming_signal[:3*ISI_LENGTH])
    print(idx, len(incoming_signal))
    decoded2 = decode_segment(incoming_signal[idx:idx+3*ISI_LENGTH])
    print([int(x) for x in decoded2[:50]])
    # TODO: handle phase shifts

# length = len(signal)
# signal_offset = list(generate_segment(data)[123]) + [0.0 + 0.0j]*(456)
# signal_offset = np.array(signal_offset[-length:], dtype=np.complex64)
