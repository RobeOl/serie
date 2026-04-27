import random
from music21 import *

def make_chord_with_min_third(A, B):
    # calcola distanza in semitoni (melodica A → B)
    semitones = interval.Interval(A, B).semitones

    # # se inferiore a 3 semitoni (terza minore)
    # if abs(semitones) < 3:
    #     B = B.transpose(12)  # alza B di un'ottava
    
    # se inferiore a 3 semitoni (terza minore)
    if abs(semitones) < 3:
        A = A.transpose(-12)  # abbassa A di un'ottava

    return chord.Chord([A, B])

def spread_chord_min_third(notes, min_semitones=3):
    # copia per non modificare gli oggetti originali
    notes = [n for n in notes]

    # ordina per altezza (MIDI)
    notes.sort(key=lambda n: n.pitch.midi)

    for i in range(1, len(notes)):
        prev = notes[i - 1]
        curr = notes[i]

        # alza finché la distanza è sufficiente
        while (curr.pitch.midi - prev.pitch.midi) < min_semitones:
            curr = curr.transpose(12)

        notes[i] = curr

    return chord.Chord(notes)

def genera_armonia(seq_type,tipo,s):
    notes=s.notes
    # left hand
    left = stream.Part()
    left.insert(0, instrument.Piano())
    left.insert(0, clef.BassClef())
    # chords based on four notes
    N = len(s)-1
    nn = 0
    while nn<N:
        X1 = copy.deepcopy(notes[nn])
        X1.octave = 3
        X2 = copy.deepcopy(notes[nn+1])
        X2.octave = 3
        X3 = copy.deepcopy(notes[nn+2])
        X3.octave = 3
        X4 = copy.deepcopy(notes[nn+3])
        X4.octave = 3
        durata = X1.duration.quarterLength
        durata = durata*4
        Cx = chord.Chord([X1,X2,X3,X4])
        Cx.duration.quarterLength = durata
        left.append(Cx)
        nn = nn+4
 
    return(left)