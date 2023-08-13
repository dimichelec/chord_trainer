

class chords:

    chart_maj = [
        [ ('C','maj'), ('D','min'), ('E','min'), ('F','maj'), ('G','maj'), ('A','min'), ('B','dim') ]
    ]

    chart_251 = [
        [ # 'to play'   detected as     diagram
          ('Cm9',       ('D#','maj'),   ('C','m9')),
          ('Fm7',       ('F','min'),    ('F','m7')),
          ('BbM7',      ('A#','maj'),   ('A#','M7')),
        ]
    ]

    # the standard tuning 3 bass strings of a guitar
    bass_tuning = ('E','A','D')
    notes = ('C','C#','D','D#','E','F','F#','G','G#','A','A#','B')

    # (chord type <M = major, m = minor> [
    #   The following pattens are in order from root note on low E string, A string...
    #   (fret pattern by string, low E first, -1 = don't play, 0 = play open),
    #   (interval of fretted strings from root, 0 = string not played, 1 = root)
    # ])

    formulas = [
        ('', [
            ((0,-1,2,1,0,-1), (1,0,1,3,5,0)),       # root on low E string
            ((-1,0,2,2,2,-1), (0,1,5,1,3,0)),       # root on A string
            ((-1,-1,0,2,3,2), (0,0,1,5,1,3))]),     # root on D string
        ('m', [
            ((0,-1,2,0,0,-1), (1,0,1,-3,5,0)),       # root on low E string
            ((-1,0,2,2,1,-1), (0,1,5,1,-3,0)),       # root on A string
            ((-1,-1,0,2,3,1), (0,0,1,5,1,-3))]),     # root on D string
        ('M7', [
            ((0,-1,1,1,0,-1), (1,0,7,3,5,0)),       # root on low E string
            ((-1,0,2,1,2,-1), (0,1,5,7,3,0)),       # root on A string
            ((-1,-1,0,2,2,2), (0,0,1,5,7,3))]),     # root on D string
        ('7', [
            ((0,-1,0,1,0,-1), (1,0,-7,3,5,0)),      # root on low E string
            ((-1,0,2,0,2,-1), (0,1,5,-7,3,0)),      # root on A string
            ((-1,-1,0,2,1,2), (0,0,1,5,-7,3))]),    # root on D string
        ('m7', [
            ((0,-1,0,0,0,-1), (1,0,-7,-3,5,0)),     # root on low E string
            ((-1,0,2,0,1,-1), (0,1,5,-7,-3,0)),     # root on A string
            ((-1,-1,0,2,1,1), (0,0,1,5,-7,-3))]),   # root on D string
        ('M9', [
            ((0,-1,1,1,2,2), (1,0,7,3,6,9)),        # root on low E string
            ((-1,1,0,2,1,-1), (0,1,3,7,9,0))]),     # root on A string
        ('9', [
            ((-1,1,0,1,1,1), (0,1,3,-7,9,5))]),     # root on A string
        ('m9', [
            ((2,0,2,1,-1,-1), (1,-3,-7,9,0,0)),     # root on low E string
            ((-1,2,0,2,2,-1), (0,1,-3,-7,9,0)),     # root on A string
            ((-1,-1,2,0,3,2), (0,0,1,-3,-7,9))]),   # root on D string
    ]


    # given the root note and chord type, return a chord from our formulas played
    # in lowest neck position
    def find_best_chord(self,root,type):

        # find the forms for the chord type
        forms = list(filter(lambda x: x[0] == type, self.formulas))[0][1]

        # find the note index of the root note
        try:
            iroot = self.notes.index(root)
        except ValueError:
            iroot = self.notes.index(root[0])-1 if ('-' in root) or ('b' in root) else iroot
            iroot += len(self.notes) if iroot < 0 else 0

        # find the form that will fit in the lowest position on the neck, based on
        # which string our root note will be on.
        # returns tuple (root string, root fret, chord form, string intervals)
        out = ()
        root_string = root_fret = iform = 0
        for open_note in self.bass_tuning:
            iopen = self.notes.index(open_note)
            root_fret = (iroot - iopen) if (iroot >= iopen) else (12 + iroot - iopen)
            try:
                if forms[iform][1][root_string] == 1:
                    form = forms[iform]
                    if root_fret < form[0][root_string]:
                        root_fret += 12
                    if (out == ()) or (root_fret < out[1]):
                        out = (root_string, root_fret, form[0], form[1])
                    iform += 1
            except:
                pass
            root_string += 1

        return out


    def diagram(self,root,type):
        out = []
        chord = self.find_best_chord(root,type)
        root_string = chord[0]
        root_fret = chord[1]
        form = chord[2]
        intervals = chord[3]
        MAX_FRETS = 5


        def interval_ascii(i):
            b = 'R' if i == 1 else str(abs(i))
            a = 'p' if i in (4,5) else ' '
            a = 'b' if i < 0 else a
            if abs(i) in (1,3,5):
                return f'\033[41;1m{a}{b} \033[0m'
            else:
                return f'\033[43;1m{a}{b} \033[0m'


        def position_ascii(position):
            out = 'th'
            if position == 1:
                out = 'st'
            elif position == 2:
                out = 'nd'
            elif position == 3:
                out = 'rd'
            return str(position) + out


        out.append(f'\033[37;1m{root + type}\033[0m')

        fret_offset = root_fret - form[root_string]
        position = 0
        if (max(form) + fret_offset) > MAX_FRETS:
            position = min(filter(lambda x:x >= 0, form)) + fret_offset

        # find the playing pattern at the nut
        line = ''
        for string,fret in enumerate(form):
            if fret == -1:  # string not played
                line += ' X '
            elif (fret+fret_offset) == 0:
                line += interval_ascii(intervals[string])
            else:
                if string == 0:
                    line += ' ▄▄' if position == 0 else ' ╟─'
                elif string == 5:
                    line += '▄▄ ' if position == 0 else '─┤ '
                else:
                    line += '▄▄▄' if position == 0 else ('─╫─' if string < 4 else '─┼─')
            if string < 5:
                line += '▄' if position == 0 else '─'

        out.append(line)
        if position == 0:
            out.append(' ╟───╫───╫───╫───┼───┤')

        ifret = position if position > 0 else 1
        while (ifret <= (max(form) + fret_offset)) or ((ifret - position) <= MAX_FRETS):
            line = ''
            for string,fret in enumerate(form):
                if (fret >= 0) and (ifret == (fret+fret_offset)):
                    line += interval_ascii(intervals[string])
                else:
                    line += ' ║ ' if string < 4 else ' │ '
                if string == 2:
                    if ifret in (3,5,7,9,15,17,19):
                        line += '●'
                    elif ifret == 12:
                        line += '○'
                    else:
                        line += ' '
                else:
                    line += ' '

            if (position != 0) and (ifret == position):
                line += ' ' + position_ascii(position)

            out.append(line)
            out.append(' ╟───╫───╫───╫───┼───┤')
            ifret += 1

        return out


    def print_chord(self,root,type):
        for line in self.diagram(root,type):
            print(line)



        
