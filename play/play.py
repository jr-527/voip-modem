import sys
from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from defs import read_pipe, log
import time
import numpy as np
import pyaudiowpatch as pyaudio
from collections import deque
from threading import Thread

SAMPLE_RATE=48000
SAMPLES_PER_BUFFER=4096
SAMPLE_BYTES=4
NUMPY_DTYPE=np.float32
PYAUDIO_TYPE=pyaudio.paFloat32

def get_data() -> np.ndarray:
    return np.frombuffer(read_pipe(SAMPLES_PER_BUFFER*SAMPLE_BYTES), dtype=NUMPY_DTYPE)

q = deque()

def place_data():
    log("Playback: Threaded stdin read starting")
    try:
        while True:
            q.appendleft(get_data())
    except:
        log("Playback: Threaded stdin read failed, winding down.")

def main():
    log("Playback: Preparing buffer.")
    try:
        for _ in range(3*SAMPLE_RATE//SAMPLES_PER_BUFFER):
            # build up a buffer so that we don't run out of data
            q.appendleft(get_data())
    except:
        pass
    log("Playback: Buffer filled out, beginning main loop.")

    thread = Thread(target=place_data)
    thread.start()

    def callback(in_data, frame_count, time_info, status):
        if q:
            return q.pop(), pyaudio.paContinue
        else:
            return np.zeros(SAMPLES_PER_BUFFER, dtype=NUMPY_DTYPE), pyaudio.paContinue

    p = pyaudio.PyAudio()
    stream = p.open(format=PYAUDIO_TYPE, rate=SAMPLE_RATE, channels=1,
                    output=True, stream_callback=callback, #type:ignore
                    frames_per_buffer=SAMPLES_PER_BUFFER)
    stream.start_stream()
    log("Playback: starting")
    try:
        while stream.is_active():
            time.sleep(0.1)
    except:
        log("Playback: done")
    try:
        thread.join()
    except:
        pass

if __name__ == '__main__':
    main()