    
import sys
import time
import config
import audio
import ui
import game
import metronome


# process command line args and load config file
config = config.config()

#  create and open the audio devices
audio = audio.audio(
    device_in  = config.input_device, device_out = config.output_device)

# create the UI
ui = ui.ui()

# create game object
game = game.game(ui)
game.reset()
game.set_chart(config.chart)

# create the metronome
metronome = metronome.metronome(
    audio, bpm=config.bpm, measures=game.chart_pos_max, chord_beats=config.chord_beats)
audio.set_metronome(metronome)

# draw UI components
ui.draw_chart(game.chart)
ui.draw_bpm(metronome.bpm)

# start the audio stream 
audio.start_stream()

onset   = False
run     = False
lead_in = 4

while audio.is_active():
    
    # beat clock
    if run:
        state, measure, beat = metronome.service()
        if state > 0:
            if lead_in > 0:
                lead_in -= 1
                if lead_in == 0:
                    metronome.reset()
            else:
                if state == 1:
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
        lead_in = 4


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
