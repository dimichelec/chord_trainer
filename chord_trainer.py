    
import sys
import time
import getopt
import ui
import audio
import metronome
import chords


# ----------------------------------------------------------------------------------------------

# process command line args

def usage(out):
    print(f'usage: {sys.argv[0]} [-b <bpm> -c <chords> -d -v <device> -h]\n')
    print('-b <bpm>,    --bpm     : set tempo to <bpm>')
    print('-c <chords>, --chords  : use comma separated list as chart (eg. "-c Am,D,Gm,C")')
    print('-d,          --devices : list all audio devices')
    print('-v <device>, --verbose : show device(s) with verbose info (eg. "-v Speaker" shows all')
    print('                         devices with "Speaker" in its name)')
    print('-h,          --help    : show usage information')
    sys.exit(out)


chart = ''
bpm = 0
try:
    opts, args = getopt.getopt(sys.argv[1:],'bc:dv:h',["bpm=","chords=","devices","verbose=","help"])

except getopt.GetoptError:
    usage(2)

for opt, arg in opts:
    if opt in ['-b', '--bpm']:
        bpm = int(arg)
    elif opt in ['-c', '--chords']:
        chart = []
        for chord in arg.split(','):
            chart.append((chord.split('m')[0], 'min' if 'm' in chord else 'maj'))
    elif opt in ['-d', '--devices']:
        audio = audio.audio()
        audio.print_devices()
        audio.uninit()
        sys.exit()
    elif opt in ['-v', '--verbose']:
        audio = audio.audio()
        audio.print_devices(filter=arg, verbose=True)
        audio.uninit()
        sys.exit()
    elif opt in ['-h', '--help']:
        usage(None)


# ----------------------------------------------------------------------------------------------


class game:
    chart           = None
    chart_pos_max   = 0
    score           = 0
    chord_score     = -1
    chord_count     = 0
    chords_right    = 0
    chord_lag_sum   = 0
    chord_lag_sum   = 0


    def __init__(self,ui):
        self.ui = ui


    def reset(self):
        self.score = 0
        self.chord_score = -1
        self.chord_count = self.chords_right = 0
        self.chord_lag = self.chord_lag_sum = 0
        self.ui.draw_chord_box()
        self.ui.draw_beatclock(1, 1)
        self.ui.draw_score('0' + 20*' ')
        self.ui.draw_chart_pointer(0)
        self.beat_start = time.perf_counter()


    def set_chart(self,chart):
        self.chart = chart
        self.chart_pos_max = len(self.chart)


    def first_beat(self,measure):
        self.ui.draw_chart_pointer(measure)
        self.ui.draw_chord(self.chart[measure-1], 0)
        self.chord_score = -1
        self.ui.draw_chord_score(30*' ')
        self.chord_count += 1


    def score_chord(self,chord,measure, beat_start):
        if self.chord_score != -1:
            return

        right = False
        self.chord_score = 0
        if self.chart[measure-1][0] == chord[0]:
            self.chord_score += 10
        if self.chart[measure-1][1] == chord[1]:
            self.chord_score += 5
        if self.chord_score == 15:
            self.chords_right += 1
            right = True
            self.ui.draw_chord(chord, 1)
        else:
            self.ui.draw_chord(chord, 2)

        a = ''
        self.chord_lag = time.perf_counter() - beat_start
        if right:
            if self.chord_lag < 1:
                self.chord_score += 1
            if self.chord_lag < 0.4:
                self.chord_score += 1
            if self.chord_lag < 0.3:
                a = 'Good'
                self.chord_score += 2
            if self.chord_lag < 0.2:
                a = 'Very Good'
                self.chord_score += 2
            if self.chord_lag < 0.1:
                a = 'Perfect!'
                self.chord_score += 3
            self.chord_lag_sum += self.chord_lag

        self.ui.draw_chord_score('+' + str(self.chord_score) + ' ' + a)
        self.score += self.chord_score



#  create and open the audio devices
audio = audio.audio(
    device_in  = 27,    # Rocksmith
    device_out = 23     # Focusrite
)

# create the UI
ui = ui.ui()

# create game object
game = game(ui)
game.reset()
game.set_chart(chords.chords.chart_maj[0] if chart == '' else chart)

# create the metronome
bpm = 110 if bpm == 0 else bpm  # use command-line requested tempo if requested
metronome = metronome.metronome(
    audio, bpm=bpm, measures=game.chart_pos_max, chord_beats=4
)
audio.set_metronome(metronome)

# draw UI components
ui.draw_chart(game.chart)
ui.draw_bpm(metronome.bpm)

# start the audio stream 
audio.start_stream()

onset   = False
run     = False
lead_in = True

while audio.is_active():
    
    # beat clock
    if run:
        state, measure, beat = metronome.service()
        if state > 0:
            if lead_in:
                if beat == 4:
                    lead_in = False
                    metronome.reset()
            else:
                if beat == 1:
                    beat_start = time.perf_counter()
                    game.first_beat(measure)
                    if game.chord_count % 100 == 0:
                        run = False

                ui.draw_beatclock(measure, beat)
                ui.draw_score(game.score)

                if game.chord_count > 0:
                    ui.draw_stats_line(1,
                          f'{game.chords_right:3d}/{game.chord_count:<3d} '
                        + ui.stats_style1 + f'{game.chords_right/game.chord_count*100:3.0f}%'
                        + ui.stats_style  + ' CHORDS RIGHT')
                if game.chords_right > 0:
                    ui.draw_stats_line(2,
                          f'{game.chord_lag*1000:4.0f} MS '
                        + f'{game.chord_lag_sum/game.chords_right*1000:6.1f} MS AVG')

    # keystroke processing
    key = ui.keyhit()
    if key == 'q':                          # quit app
        break
    elif key == '+':                        # BPM +1
        metronome.add(1)
        ui.draw_bpm(metronome.bpm)
    elif key == '-':                        # BPM -1
        metronome.add(-1)
        ui.draw_bpm(metronome.bpm)
    elif key == ' ':                        # start/stop metronome
        run = True if not run else False
    elif key == 'r':                        # reset game
        metronome.reset()
        game.reset()
        lead_in = True


    #  1 = spectral flux over on threshold
    # -1 = spectral flux under off threshold
    os = audio.get_onset()

    if os == 1 and not onset:   # spectral flux over on threshold
        audio.start_chord_sampling()
        onset = True
        ui.draw_signal(True)
    elif os == -1 and onset:    # spectral flux under off threshold
        onset = False
        ui.draw_signal(False)

    # check for a chord
    chord = audio.get_chord()
    if chord:
        if run:
            game.score_chord(chord,measure,beat_start)
        else:
            ui.draw_chord(chord, 3)


ui.uninit()
audio.uninit()

sys.exit()
