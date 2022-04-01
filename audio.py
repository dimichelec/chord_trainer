
import numpy as np
import scipy
from scipy import signal
import pyaudio
import madmom
from madmom.audio.chroma import DeepChromaProcessor
from madmom.processors import SequentialProcessor
from madmom.features.chords import DeepChromaChordRecognitionProcessor
from pprint import pprint
import re


class audio:

    # ----------------------------------------------------------------------------------------------
    #  Constants
    #
    WINDOW_SIZE = 48000         # window size of the DFT in samples
    #ONSET_ON_THRESH = 1e-4      # spectral flux threshold to determine event onset
    #ONSET_OFF_THRESH = 3e-5     # spectral flux threshold to determine event end

    ONSET_ON_THRESH = 2e-4      # spectral flux threshold to determine event onset
    ONSET_OFF_THRESH = 4e-5     # spectral flux threshold to determine event end

    MIN_ONSET_SAMPLES = 40      # samples to collect after onset before chordrec


    # print the set of input or output audio devices
    def print_device_set(self, inout, filter=None, verbose=False):
        for device in range (self.audioinstance.get_device_count()):
            ins    = self.audioinstance.get_device_info_by_index(device)['maxInputChannels']
            outs   = self.audioinstance.get_device_info_by_index(device)['maxOutputChannels']
            rate   = self.audioinstance.get_device_info_by_index(device)['defaultSampleRate']
            inlat  = self.audioinstance.get_device_info_by_index(device)['defaultHighInputLatency']
            outlat = self.audioinstance.get_device_info_by_index(device)['defaultHighOutputLatency']
            name   = self.audioinstance.get_device_info_by_index(device)['name']
            name   = re.sub(r'[\r,\n]+',' ', name)
            if inout == 0:  # input devices
                if filter is None or filter in name:
                    if ins > 0 or verbose:
                        if verbose:
                            print()
                        print(f'{device}: {name} - {rate/1000:.1f}kHz - {inlat*1000:.0f}ms')
                        if verbose:
                            pprint(self.audioinstance.get_device_info_by_index(device), indent=2)
            else:   # output devices
                if filter is None or filter in name:
                    if outs > 0 or verbose:
                        if verbose:
                            print()
                        print(f'{device}: {name} - {rate/1000:.1f}kHz - {outlat*1000:.0f}ms')
                        if verbose:
                            pprint(self.audioinstance.get_device_info_by_index(device), indent=2)


    # print basic device list
    def print_devices(self, io=None, filter=None, verbose=False):
        if io in [None, 0]:
            print("\nIns:")
            self.print_device_set(0, filter, verbose)
        if io in [None, 1]:
            print("\nOuts:")
            self.print_device_set(1, filter, verbose)


    # get fastest devices by latency
    def get_fastest_devices(self, inout, filter=None):
        devices = []
        for device in range (self.audioinstance.get_device_count()):
            ins    = self.audioinstance.get_device_info_by_index(device)['maxInputChannels']
            outs   = self.audioinstance.get_device_info_by_index(device)['maxOutputChannels']
            rate   = self.audioinstance.get_device_info_by_index(device)['defaultSampleRate']
            inlat  = self.audioinstance.get_device_info_by_index(device)['defaultHighInputLatency']
            outlat = self.audioinstance.get_device_info_by_index(device)['defaultHighOutputLatency']
            name   = self.audioinstance.get_device_info_by_index(device)['name']
            name   = re.sub(r'[\r,\n]+',' ', name)
            if inout == 0:  # input devices
                if (filter is None or filter in name) and ins > 0:
                    devices.append((int(inlat*1000), device, name[:25], rate))
                    #print(f'{device}: {name} - {rate/1000:.1f}kHz - {inlat*1000:.0f}ms')
            else:   # output devices
                if (filter is None or filter in name) and outs > 0:
                    devices.append((int(outlat*1000), device, name[:25], rate))
                    #print(f'{device}: {name} - {rate/1000:.1f}kHz - {outlat*1000:.0f}ms')
        devices.sort()
        return devices


    def callback(self, in_data, frame_count, time_info, status):
        
        in_data = np.frombuffer(in_data, dtype=np.int16)

        self.window_samples = np.concatenate((self.window_samples, in_data))  # append new samples
        self.window_samples = self.window_samples[len(in_data):]              # remove old samples

        # if we've triggered chord recognition from onset detection,
        # start collecting the recog sample
        if self.sample_chord:
            self.chord_sample = np.concatenate((self.chord_sample, in_data))

        # mix-in metronome click if it's on
        if self.metronome.click_flag:
            if self.metronome.click_pos < (self.metronome.click_frames_n[self.metronome.click_index] - frame_count):
                in_data = in_data + self.metronome.click_data[self.metronome.click_index][
                    self.metronome.click_pos:self.metronome.click_pos + frame_count]
                self.metronome.click_pos += frame_count
            else:
                in_data = in_data + np.pad(
                    self.metronome.click_data[self.metronome.click_index][self.metronome.click_pos:],
                    [0, frame_count - (self.metronome.click_frames_n[self.metronome.click_index] - self.metronome.click_pos)])
                self.metronome.click_flag = False
                self.metronome.click_pos = 0

        return (in_data, pyaudio.paContinue)


    def __init__(self, device_in=None, device_out=None):
        self.audioinstance = pyaudio.PyAudio()

        if device_in == None or device_out == None:
            return

        self.device_in = device_in
        self.device_out = device_out

        self.sampling_rate = int(
            self.audioinstance.get_device_info_by_index(self.device_in)['defaultSampleRate']
        )
        self.chunk_size = 512

        # create chord recognition processor
        self.chordrec_proc = SequentialProcessor([ 
            DeepChromaProcessor(), DeepChromaChordRecognitionProcessor() 
        ])

        # setup stream
        self.window_samples = [0 for _ in range(self.WINDOW_SIZE)]
        self.chord_sample = []
        self.sample_chord = False

        self.stream = self.audioinstance.open(
            format=pyaudio.paInt16,
            channels=1,
            input_device_index=self.device_in,
            output_device_index=self.device_out,
            rate=self.sampling_rate,
            input = True,
            output = True,
            frames_per_buffer = self.chunk_size,
            stream_callback = self.callback
        )


    def set_metronome(self,metronome):
        self.metronome = metronome


    def start_stream(self):
        self.stream.start_stream()


    def is_active(self):
        return self.stream.is_active()


    def get_onset(self):

        if max(self.window_samples) == 0:
            return 0

        spec = madmom.audio.spectrogram.Spectrogram(self.window_samples)
        #spec = madmom.audio.spectrogram.LogarithmicFilteredSpectrogram(
        #    window_samples, num_channels=1, sample_rate=48000,
        #    fps=10, frame_size=8192, num_bands=24, fmin=65, fmax=2100, unique_filters=True
        #)
        
        diff = np.diff(spec, axis=0)
        pos_diff = np.maximum(0, diff)
        sf = np.sum(pos_diff, axis=1)

        if sf[-2] > self.ONSET_ON_THRESH:
            return 1

        if sf[-2] < self.ONSET_OFF_THRESH:
            return -1
        
        return 0


    def start_chord_sampling(self):
        self.chord_sample = []
        self.sample_chord = True


    def get_chord(self):
        if self.sample_chord and (len(self.chord_sample) > self.MIN_ONSET_SAMPLES):

            # madmon only works at 44100 Hz, resample
            chords = self.chordrec_proc(
                scipy.signal.resample(
                    self.chord_sample, int(len(self.chord_sample)/self.sampling_rate*44100)
                )
            )
            
            for chord in chords:
                if chord[2] != 'N':
                    self.sample_chord = False
                    return chord[2].split(':')

        return ''


    def uninit(self):
        try:
            # stop stream 
            self.stream.stop_stream()
            self.stream.close()
        except:
            pass
        
        # close PyAudio 
        self.audioinstance.terminate()

