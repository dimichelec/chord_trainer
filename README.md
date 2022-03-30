# chord_trainer

chord_trainer is an open source game I made to help with practicing guitar chords written in Python.

chord_trainer uses the [madmom](https://github.com/CPJKU/madmom) audio signal processing library to recognize audio onset and chord recognition.


# usage

  usage: chord_trainer.py [-b <bpm> -c <chords> -d -v <device> -h]

  -b <bpm>,    --bpm     : set tempo to <bpm>
  -c <chords>, --chords  : use comma separated list as chart (eg. "-c Am,D,Gm,C")
  -d,          --devices : list all audio devices
  -v <device>, --verbose : show device(s) with verbose info (eg. "-v Speaker" shows all
                           devices with "Speaker" in its name)
  -h,          --help    : show usage information

  
  

written by [Carmen DiMichele](https://dimichelec.wixsite.com/carmendimichele) 

