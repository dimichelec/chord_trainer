
import time


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
        self.ui.draw_stats_line(1,40*' ')
        self.ui.draw_stats_line(2,40*' ')
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
