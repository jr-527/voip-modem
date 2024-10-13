import sys
from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from defs import write_pipe, log
import pyaudiowpatch as pyaudio # Windows only. python -m pip install PyAudioWPatch
import time
import numpy as np

def output_audio(func, batch_size=4096, num_format="short"):
    """
    func: Whenever we have data, we'll call
    func(data)
    where data is a numpy array
    output_size: T
    """
    if num_format == "float":
        data_format = pyaudio.paFloat32
        np_dtype = np.float32
    else:
        assert num_format == "short"
        data_format = pyaudio.paInt16
        np_dtype = np.int16
    p = pyaudio.PyAudio()
    speakers = p.get_default_wasapi_loopback()
    log(f"Recording: Input device details: {speakers}")
    fs = int(speakers["defaultSampleRate"])
    log(f"Recording: sampling_rate = {fs}, format={num_format}")
    def _callback_wrapper(in_data, frame_count, time_info, flag):
        func(np.frombuffer(in_data, dtype=np_dtype)) # type:ignore
        return in_data, pyaudio.paContinue
    stream = p.open(format=data_format, channels=1, rate=fs, output=False, input=True,
                    input_device_index=speakers["index"], frames_per_buffer=batch_size,
                    stream_callback=_callback_wrapper)
    log("Recording: Starting")
    stream.start_stream()
    try:
        while stream.is_active():
            time.sleep(0.1)
    except:
        pass
    log("Recording: Done")


def my_func(data: np.ndarray):
    write_pipe(data.tobytes())

def main():
    output_audio(my_func, batch_size=4096, num_format="float")

if __name__ == '__main__':
    main()
