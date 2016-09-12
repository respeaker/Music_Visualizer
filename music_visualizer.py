"""
 Music Player with Spectrum
 Copyright (c) 2016 Seeed Technology Limited.

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
"""

import sys
import threading
import Queue
import time
import wave
import audioop
import math

import pyaudio
from spectrum_analyzer import SpectrumAnalyzer

FRAMES = 1024
DELAY_N = 0
BARS = 12


class Player:
    def __init__(self):
        self.analyzer = SpectrumAnalyzer(FRAMES, band_number=BARS)
        self.pyaudio_instance = pyaudio.PyAudio()
        self.queue = Queue.Queue()
        self.event = threading.Event()
        self.delay_queue = Queue.Queue()

    def play(self, wav_file, quit_event=None, show=None):
        self.wav = wave.open(wav_file, 'rb')
        channels = self.wav.getnchannels()
        if channels > 2:
            raise Exception('%d channels not supported' % channels)
        stream = self.pyaudio_instance.open(
            format=self.pyaudio_instance.get_format_from_width(self.wav.getsampwidth()),
            channels=channels,
            rate=self.wav.getframerate(),
            output=True,
            # output_device_index=1,
            stream_callback=self._callback,
            frames_per_buffer=FRAMES)

        self.event.clear()
        if not quit_event:
            quit_event = threading.Event()
        while not (quit_event.is_set() or self.event.is_set()):
            try:
                data = self.queue.get()
                count = 0
                while not self.queue.empty():
                    data = self.queue.get()
                    count += 1

                if channels == 2:
                    data = audioop.tomono(data, 2, 0.5, 0.5)
                strength = self.analyzer.analyze(data)
                level = bytearray(len(strength))
                for i, v in enumerate(strength):
                    l = int(
                        v / 1024 / 128 * (3 - math.pow(i - (BARS - 1) / 2.0, 2) * 2 / math.pow((BARS - 1) / 2.0, 2)))
                    if l > 255:
                        l = 255
                    level[i] = l

                if show:
                    show(level)
                # print [l for l in level]
            except KeyboardInterrupt:
                break

        show(bytearray(len(strength)))
        stream.close()

    def _callback(self, in_data, frame_count, time_info, status):
        data = self.wav.readframes(frame_count)
        if self.wav.getnframes() == self.wav.tell():
            if data is None:
                data = '\x00' * (frame_count * self.wav.getsampwidth() * self.wav.getnchannels())
            else:
                data = data.ljust(frame_count * self.wav.getsampwidth() * self.wav.getnchannels(), '\x00')
            self.event.set()

        self.delay_queue.put(data)
        if self.delay_queue.qsize() >= DELAY_N:
            d = self.delay_queue.get()
            self.queue.put(d)

        return data, pyaudio.paContinue


def main():
    from PySide import QtGui
    from bar_widget import BarWidget

    app = QtGui.QApplication(sys.argv)
    widget = BarWidget()
    widget.setWindowTitle('Music Visualizer')
    widget.show()

    song = sys.argv[1] if len(sys.argv) > 1 else 'where_is_love.wav'
    player = Player()

    quit_event = threading.Event()
    thread = threading.Thread(target=player.play, args=(song, quit_event, widget.setBars))
    thread.start()

    app.exec_()

    quit_event.set()
    thread.join()

if __name__ == '__main__':
    main()

