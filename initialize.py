import pyaudiowpatch as pyaudio
import numpy as np
import sys
import time

def get_devices(defaults: dict = {}) -> None|dict[str, dict]:
    p = pyaudio.PyAudio()

    input_devices = {}
    output_devices = {}

    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        # print(f"Device {i}: {info['name']}, Input: {info['maxInputChannels']}, Output: {info['maxOutputChannels']}")
        if info["maxInputChannels"]:
            input_devices[i] = info
        if info["maxOutputChannels"]:
            output_devices[i] = info
    default_loopback = p.get_default_wasapi_loopback()
    p.terminate()
    needs_abort = False
    if len(input_devices) == 0:
        print("Error: No input devices detected.")
        needs_abort = True
    if len(output_devices) == 0:
        print("Error: No output devices detected.")
        needs_abort = True
    if needs_abort:
        print("You don't have the right setup, exiting.")
        return
    if defaults.get("input"):
        defaults["input"]
    
    print("Available input devices:")
    for i, info in input_devices.items():
        print('Device {index: <5}"{name}" ({fs} KHz)'.format(index=i, name=info["name"], fs=info["defaultSampleRate"]/1000))
    print("Input the number of the device that incoming audio will play from.")
    print('You probably want one of the devices labeled "[Loopback]"')
    print(f"You might want your default device, number {default_loopback['index']}")
    try:
        input_device = int(input("\nEnter incoming audio device: "))
        if input_device not in input_devices:
            raise ValueError
    except ValueError:
        print("Not a valid input device. Exiting.")
        return

    print("Available output devices:")
    for i, info in output_devices.items():
        print('Device {index: <5}"{name}" ({fs} KHz)'.format(index=i, name=info["name"], fs=info["defaultSampleRate"]/1000))
    print("Input the number of the device that outgoing audio should be played to.")
    print("You probably want to pick one that corresponds to the Stereo Mix from")
    print("the input devices.")
    print("There may be duplicates. I'm not sure why, but the last duplicate is")
    print("usually the right one.")
    try:
        output_device = int(input("\nEnter outgoing audio device: "))
        if output_device not in output_devices:
            raise ValueError
    except ValueError:
        print("Not a valid output device. Exiting.")
        return

    return {"input":input_devices[input_device], "output":output_devices[output_device]} 

class DeviceTester:
    def __init__(self, devices):
        self.input_device = devices["input"]
        self.output_device = devices["output"]
        self.prev_rmse = 0.0
        self.fall_rate_db_per_s = 10
        self.decay_factor = 0.7
        self.t = 0

    def print_volume(self, num_symbols: int):
        print("\r\033[K", end="")
        print("volume:", ''.join(['>']*num_symbols), end="")
        sys.stdout.flush()

    def _recording_callback(self, in_data, frame_count, time_info, flag):
        arr = np.frombuffer(in_data, dtype=np.int16)
        arr = arr * 1.0
        rmse = (np.sqrt(np.mean(arr**2)) + self.decay_factor * self.prev_rmse)/2
        prev_rmse = rmse
        print("\r\033[K", end="")
        if rmse == 0:
            dB = -999
        else:
            dB = 10*np.log10(rmse/2**15)
        tmp = (dB+30)*3
        if tmp < 0:
            tmp = 0
        number_symbols = int(tmp)
        self.print_volume(number_symbols)
        return in_data, pyaudio.paContinue

    def test_input_device(self, duration:int=10):
        self.prev_rmse = 0
        fs = int(self.input_device["defaultSampleRate"])
        batch_size = 1024
        # decay_factor ** (fs/batch_size) == 0.01
        # fs/batch_size = log(.01)/log(decay_factor)
        # log(decay_factor) = log(.01)/(fs/batch_size)
        # self.decay_factor = np.exp(np.log(10**-self.fall_rate_db_per_s/10)/fs*batch_size)
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=fs, output=False,
                        input=True, input_device_index=self.input_device["index"],
                        frames_per_buffer=1024, stream_callback=self._recording_callback)
        stream.start_stream()
        if duration > 0:
            time.sleep(duration)
        elif duration == -1:
            try:
                while 1:
                    time.sleep(.1)
            except KeyboardInterrupt:
                pass
        stream.close()
        p.terminate()
    

    def _playback_callback(self, in_data, frame_count, time_info, flag):
        arr = np.arange(4096)
        t = arr/48000
        first, second = self._next_chirp_freqs()
        ft = first + (arr/len(arr)) * (second-first)
        out = np.sin(ft*2*np.pi*t, dtype=np.float32)/50
        return (out, pyaudio.paContinue)


    def _next_chirp_freqs(self) -> tuple[float, float]:
        first = 600 + 200 * np.sin(self.t/10)
        self.t += 1
        second = 600 + 200 * np.sin(self.t/10)
        return (first, second)

    def test_output_device(self, duration:int=10):
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paFloat32, rate=48000, channels=1, output=True,
                        stream_callback=self._playback_callback,
                        output_device_index=self.output_device["index"],
                        frames_per_buffer=4096)
        stream.start_stream()
        if duration > 0:
            time.sleep(duration)
        else:
            try:
                while 1:
                    time.sleep(.1)
            except KeyboardInterrupt:
                pass
        stream.stop_stream()
        p.terminate()

def main() -> tuple[int, int]:
    x = get_devices()
    if x is None:
        raise RuntimeError("Could not detect audio devices, aborting.")
    dt = DeviceTester(x)
    print("Press control-c to exit input volume test")
    dt.test_input_device(-1)
    print("\nPress control-c to exit output playback test")
    dt.test_output_device(-1)
    input_index = dt.input_device["index"]
    output_index = dt.output_device["index"]
    return input_index, output_index

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass