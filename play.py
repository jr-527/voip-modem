from queue import Queue
from piped_worker import PipedConsumer
import numpy as np
import pyaudiowpatch as pyaudio
import time
from os import _exit

class PlaybackWorker(PipedConsumer):
    interrupt = False
    def __init__(self, device_idx: int, sample_rate: int=48000,
                 samples_per_buffer: int=4096, buffer_count = 4):
        self.device_idx = device_idx
        self.sample_rate = sample_rate
        self.samples_per_buffer = samples_per_buffer
        self.buffer_count = buffer_count
        self.q = Queue()
        for i in range(buffer_count):
            self.q.put(np.zeros(samples_per_buffer, dtype=np.float32))


    def run(self):
        def callback(in_data, frame_count, time_info, status):
            if self.q:
                return self.q.get(), pyaudio.paContinue
            else:
                return np.zeros(self.samples_per_buffer, dtype=np.float32), pyaudio.paContinue

        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paFloat32, rate=self.sample_rate, channels=1,
                        output_device_index=self.device_idx,
                        output=True, stream_callback=callback, #type:ignore
                        frames_per_buffer=self.samples_per_buffer)
        stream.start_stream()
        try:
            while (not self.interrupt) and stream.is_active():
                time.sleep(0.101)
        except KeyboardInterrupt:
            exit()


    def push(self, data: np.ndarray):
        self.q.put(data)
    

    def stop(self):
        self.interrupt = True


    def __del__(self):
        self.stop()
