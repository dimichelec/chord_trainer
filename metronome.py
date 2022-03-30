
import time
from typing import MutableMapping
import wave
import numpy as np


class metronome:

    bpm     = 80
    bpm_min = 60
    bpm_max = 160
    mute    = False

    def __init__(self, audio, bpm, measures, chord_beats):
        self.audio = audio
        self.bpm = bpm
        self.measures = measures
        self.chord_beats = chord_beats
        self.T = 60/self.bpm
        self.last_T = time.perf_counter()
        self.beat = 0
        self.measure = 1

        # load a click wave for the metronome
        self.click_frames_n = []
        self.click_data = []

        click_wave = wave.open("Bb Click.wav", 'rb')
        self.click_frames_n.append(click_wave.getnframes())
        click_frames = click_wave.readframes(self.click_frames_n[0])
        self.click_data.append(np.frombuffer(click_frames, dtype=np.int16))
        self.click_data[0] = self.click_data[0] // 6

        # make a second copy of click wave that's 1/3 the volume
        # this is for the non-accented beats
        self.click_data.append(self.click_data[0] // 3)
        self.click_frames_n.append(click_wave.getnframes())

        self.click_pos = 0
        self.click_index = 0
        self.click_flag   = False


    def service(self):
        if (time.perf_counter() - self.last_T) < self.T:
            return 0, self.measure, self.beat

        self.last_T = time.perf_counter()
        if not self.mute:
            self.click_index = 0 if self.beat in [0, self.chord_beats] else 1
            self.click_flag = True

        self.beat += 1
        if self.beat > self.chord_beats:
            self.beat = 1
            self.measure += 1
            if self.measure > self.measures:
                self.measure = 1
        return 1, self.measure, self.beat


    def reset(self):
        self.beat = 0
        self.measure = 1


    def add(self,amount):
        self.bpm += amount
        if self.bpm > self.bpm_max:
            self.bpm = self.bpm_max
        elif self.bpm < self.bpm_min:
            self.bpm = self.bpm_min
        self.T = 60/self.bpm


