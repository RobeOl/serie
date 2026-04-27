from music21 import *
import copy

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

def genera_armonia(seq_type,harmony_type,s):
    if seq_type=="Binary":
        notes=s.notes
        # left hand
        N = len(notes)-1
        nn = 0
        left = stream.Part()
        # chords based on two notes      
        while nn<N:
            X1 = copy.deepcopy(notes[nn])
            X1.octave = 3
            X2 = copy.deepcopy(notes[nn+1])
            X2.octave = 3
            durata = X1.duration.quarterLength
            durata = durata*2
            Cx = chord.Chord([X1,X2])
            Cx.duration.quarterLength = durata
            left.append(Cx)
            nn = nn+2 
        left.append(notes[1])
    elif seq_type=="Quaternary":
        notes=s.notes
        # left hand
        N = len(notes)-1
        nn = 0
        left = stream.Part()
        if harmony_type=="classic":
            # chords based on four notes      
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
        elif harmony_type=="onbeat":
            # chords based on two notes (1-3 and 2-4)
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
                durata = durata*2
                Cx = make_chord_with_min_third(X1, X3)
                Cx.duration.quarterLength = durata
                left.append(Cx)
                Cx = make_chord_with_min_third(X2, X4)
                Cx.duration.quarterLength = durata
                left.append(Cx)
                nn = nn+4
        elif harmony_type=="offbeat":
            # chords based on two notes (2-4 and 1-3)
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
                durata = durata*2
                Cx = make_chord_with_min_third(X2, X4)
                Cx.duration.quarterLength = durata
                left.append(Cx)
                Cx = make_chord_with_min_third(X1, X3)
                Cx.duration.quarterLength = durata
                left.append(Cx)
                nn = nn+4
        # last note = first note
        left.append(notes[1])
    return(left)