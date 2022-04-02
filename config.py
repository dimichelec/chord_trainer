
import sys
import getopt
import audio
import chords
import configparser


def usage(out):
    print(f'usage: {sys.argv[0]} -i <device ID> -o <device ID> -b <bpm> -c <chords> -d -v <device> -h\n')
    print('-i <device ID>, --input   : use this device ID for input')
    print('-o <device ID>, --output  : use this device ID for output')
    print('-b <bpm>,       --bpm     : set tempo to <bpm>')
    print('-c <chords>,    --chords  : use comma separated list as chart (eg. "-c Am,D,Gm,C")')
    print('-d,             --devices : list all audio devices')
    print('-e <beats>,     --beats   : beats per chord')
    print('-v <device>,    --verbose : show device(s) with verbose info (eg. "-v Speaker" shows all')
    print('                            devices with "Speaker" in its name)')
    print('-h,             --help    : show usage information')
    print('\nchord_trainer.ini could also be used to set any of these parameters and more.')
    sys.exit(out)


class config:
    chart = chords.chords.chart_maj[0]
    bpm = 110
    input_device = -1
    output_device = -1
    chord_beats = 4


    def __init__(self):

        # check for a config file and parse it first
        config = configparser.ConfigParser()
        config.read("chord_trainer.ini")
        for section in config.sections():
            for key in config[section]:
                arg = config[section][key].split('#')[0]
                if key == 'input':
                    self.input_device = int(arg)
                elif key == 'output':
                    self.output_device = int(arg)
                elif key == 'bpm':
                    self.bpm = int(arg)
                elif key == 'chords':
                    self.chart = []
                    for chord in arg.split(','):
                        self.chart.append((chord.split('m')[0], 'min' if 'm' in chord else 'maj'))
                elif key == 'chord_beats':
                    self.chord_beats = int(arg)

        # process any command line args
        try:
            opts, args = getopt.getopt(sys.argv[1:],'i:o:b:c:de:v:h',
                ["input=","output=","bpm=","chords=","devices","beats=","verbose=","help"])

        except getopt.GetoptError:
            usage(2)

        for opt, arg in opts:
            if opt in ['-i', '--input']:
                self.input_device = int(arg)
            elif opt in ['-o', '--output']:
                self.output_device = int(arg)
            elif opt in ['-b', '--bpm']:
                self.bpm = int(arg)
            elif opt in ['-c', '--chords']:
                self.chart = []
                for chord in arg.split(','):
                    self.chart.append((chord.split('m')[0], 'min' if 'm' in chord else 'maj'))
            elif opt in ['-d', '--devices']:
                self.audio = audio.audio()
                self.audio.print_devices()
                self.audio.uninit()
                sys.exit()
            elif opt in ['-e', '--beats']:
                self.chord_beats = int(arg)
            elif opt in ['-v', '--verbose']:
                self.audio = audio.audio()
                self.audio.print_devices(filter=arg, verbose=True)
                self.audio.uninit()
                sys.exit()
            elif opt in ['-h', '--help']:
                usage(None)


        if self.input_device == -1 or self.output_device == -1:
            print('Input and output devices need to be defined. \n')
            usage(2)

        


