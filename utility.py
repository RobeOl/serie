import random
from music21 import *

def f_octave(x, ottave, oct):
    oct_max = oct + ottave  # ottava massima consentita

    # Correggi se troppo alta
    while x.octave > oct_max:
        x.octave -= 1

    # Correggi se troppo bassa
    while x.octave < oct:
        x.octave += 1

def f_durata(x):
    x.duration.quarterLength = random.choice([1, 1/2, 1/4])

