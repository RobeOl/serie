from music21 import *
import copy

def make_chord_with_min_third(A, B):
    # calcola distanza in semitoni (melodica A → B)
    semitones = interval.Interval(A, B).semitones

    # se inferiore a 3 semitoni (terza minore)
    if abs(semitones) < 3:
        A = A.transpose(-12)  # abbassa A di un'ottava

    return chord.Chord([A, B])


def fill_to_measure(left, beats_per_measure=4):
    # Aggiunge una pausa finale per completare l'ultima battuta.
    total = sum(el.duration.quarterLength for el in left.notesAndRests)
    position_in_measure = total % beats_per_measure
    if position_in_measure > 0:
        remainder = beats_per_measure - position_in_measure
        r = note.Rest()
        r.duration.quarterLength = remainder
        left.append(r)


def add_final_chord(left, notes, N):
    # Aggiunge il bicordo finale: ultima nota una e due ottave sotto.
    last = copy.deepcopy(notes[N])
    low1 = copy.deepcopy(notes[N])
    low2 = copy.deepcopy(notes[N])
    low1.octave = last.octave - 1
    low2.octave = last.octave - 2
    Cf = chord.Chord([low2, low1])
    Cf.duration.quarterLength = last.duration.quarterLength
    left.append(Cf)


def genera_armonia_coppie(s):
    # Armonizzazione per coppie consecutive, indipendente da seq_type e harmony_type.
    # Usata per tempo free e length-constrained.
    left = stream.Part()

    # check se inizia con pausa, perché proveniente da Retrograde
    for el in s.notesAndRests:
        if el.isRest:
            left.append(el)
        else:
            break

    notes = s.notes
    N = len(notes) - 1
    nn = 0

    while nn < N:
        X1 = copy.deepcopy(notes[nn])
        X1.octave = 3
        X2 = copy.deepcopy(notes[nn + 1])
        X2.octave = 3
        durata = X1.duration.quarterLength + X2.duration.quarterLength
        Cx = chord.Chord([X1, X2])
        Cx.duration.quarterLength = durata
        left.append(Cx)
        nn = nn + 2

    # bicordo finale: ultima nota una e due ottave sotto
    # bicordo finale solo se le note sono in numero dispari
    if N % 2 == 0:
        add_final_chord(left, notes, N)

    # pausa per completare l'ultima battuta
    fill_to_measure(left)

    return left


def genera_armonia(seq_type, harmony_type, s):
    # caso binary
    if seq_type == "Binary":
        left = stream.Part()
        # check se inizia con pausa, perché proveniente da Retrograde
        for el in s.notesAndRests:
            if el.isRest:
                left.append(el)
            else:
                break

        notes = s.notes
        N = len(notes) - 1
        nn = 0

        # accordi su coppie di note
        while nn < N:
            X1 = copy.deepcopy(notes[nn])
            X1.octave = 3
            X2 = copy.deepcopy(notes[nn + 1])
            X2.octave = 3
            durata = X1.duration.quarterLength + X2.duration.quarterLength
            Cx = chord.Chord([X1, X2])
            Cx.duration.quarterLength = durata
            left.append(Cx)
            nn = nn + 2

        # bicordo finale: ultima nota una e due ottave sotto
        add_final_chord(left, notes, N)

        # pausa per completare l'ultima battuta
        fill_to_measure(left)

    # caso quaternary
    elif seq_type == "Quaternary":
        left = stream.Part()
        # check se inizia con pausa, perché proveniente da Retrograde
        for el in s.notesAndRests:
            if el.isRest:
                left.append(el)
            else:
                break

        notes = s.notes
        N = len(notes) - 1
        nn = 0

        if harmony_type == "classic":
            # accordi su quattro note
            while nn + 3 <= N:
                X1 = copy.deepcopy(notes[nn])
                X1.octave = 3
                X2 = copy.deepcopy(notes[nn + 1])
                X2.octave = 3
                X3 = copy.deepcopy(notes[nn + 2])
                X3.octave = 3
                X4 = copy.deepcopy(notes[nn + 3])
                X4.octave = 3
                durata = (X1.duration.quarterLength + X2.duration.quarterLength +
                          X3.duration.quarterLength + X4.duration.quarterLength)
                Cx = chord.Chord([X1, X2, X3, X4])
                Cx.duration.quarterLength = durata
                left.append(Cx)
                nn = nn + 4

        elif harmony_type == "onbeat":
            # accordi su due note (1-3 e 2-4)
            while nn + 3 <= N:
                X1 = copy.deepcopy(notes[nn])
                X1.octave = 3
                X2 = copy.deepcopy(notes[nn + 1])
                X2.octave = 3
                X3 = copy.deepcopy(notes[nn + 2])
                X3.octave = 3
                X4 = copy.deepcopy(notes[nn + 3])
                X4.octave = 3
                durata13 = X1.duration.quarterLength + X3.duration.quarterLength
                durata24 = X2.duration.quarterLength + X4.duration.quarterLength
                Cx = make_chord_with_min_third(X1, X3)
                Cx.duration.quarterLength = durata13
                left.append(Cx)
                Cx = make_chord_with_min_third(X2, X4)
                Cx.duration.quarterLength = durata24
                left.append(Cx)
                nn = nn + 4

        elif harmony_type == "offbeat":
            # accordi su due note (2-4 e 1-3)
            while nn + 3 <= N:
                X1 = copy.deepcopy(notes[nn])
                X1.octave = 3
                X2 = copy.deepcopy(notes[nn + 1])
                X2.octave = 3
                X3 = copy.deepcopy(notes[nn + 2])
                X3.octave = 3
                X4 = copy.deepcopy(notes[nn + 3])
                X4.octave = 3
                durata24 = X2.duration.quarterLength + X4.duration.quarterLength
                durata13 = X1.duration.quarterLength + X3.duration.quarterLength
                Cx = make_chord_with_min_third(X2, X4)
                Cx.duration.quarterLength = durata24
                left.append(Cx)
                Cx = make_chord_with_min_third(X1, X3)
                Cx.duration.quarterLength = durata13
                left.append(Cx)
                nn = nn + 4
            
        # bicordo finale: ultima nota una e due ottave sotto
        add_final_chord(left, notes, N)

        # pausa per completare l'ultima battuta
        fill_to_measure(left)

    # caso senary
    elif seq_type == "Senary":
        left = stream.Part()
        # check se inizia con pausa, perché proveniente da Retrograde
        for el in s.notesAndRests:
            if el.isRest:
                left.append(el)
            else:
                break

        notes = s.notes
        N = len(notes) - 1
        nn = 0

        if harmony_type == "classic":
            # accordi su tre note (una si una no dell'esacordo)
            while nn < N:
                X1 = copy.deepcopy(notes[nn])
                X1.octave = 3
                X2 = copy.deepcopy(notes[nn + 1])
                X2.octave = 3
                X3 = copy.deepcopy(notes[nn + 2])
                X3.octave = 3
                X4 = copy.deepcopy(notes[nn + 3])
                X4.octave = 3
                X5 = copy.deepcopy(notes[nn + 4])
                X5.octave = 3
                X6 = copy.deepcopy(notes[nn + 5])
                X6.octave = 3
                durata = (X1.duration.quarterLength + X2.duration.quarterLength +
                          X3.duration.quarterLength + X4.duration.quarterLength +
                          X5.duration.quarterLength + X6.duration.quarterLength)
                Cx = chord.Chord([X1, X3, X5])
                Cx.duration.quarterLength = durata
                left.append(Cx)
                nn = nn + 6

        elif harmony_type == "onbeat":
            # accordi su tre note (1-3-5 e 2-4-6)
            while nn + 5 <= N:
                X1 = copy.deepcopy(notes[nn])
                X1.octave = 3
                X2 = copy.deepcopy(notes[nn + 1])
                X2.octave = 3
                X3 = copy.deepcopy(notes[nn + 2])
                X3.octave = 3
                X4 = copy.deepcopy(notes[nn + 3])
                X4.octave = 3
                X5 = copy.deepcopy(notes[nn + 4])
                X5.octave = 3
                X6 = copy.deepcopy(notes[nn + 5])
                X6.octave = 3
                durata135 = X1.duration.quarterLength + X3.duration.quarterLength + X5.duration.quarterLength
                durata246 = X2.duration.quarterLength + X4.duration.quarterLength + X6.duration.quarterLength
                Cx = chord.Chord([X1, X3, X5])
                Cx.duration.quarterLength = durata135
                left.append(Cx)
                Cx = chord.Chord([X2, X4, X6])
                Cx.duration.quarterLength = durata246
                left.append(Cx)
                nn = nn + 6

        elif harmony_type == "offbeat":
            # accordi su due note (2-4 e 1-3)
            while nn + 5 <= N:
                X1 = copy.deepcopy(notes[nn])
                X1.octave = 3
                X2 = copy.deepcopy(notes[nn + 1])
                X2.octave = 3
                X3 = copy.deepcopy(notes[nn + 2])
                X3.octave = 3
                X4 = copy.deepcopy(notes[nn + 3])
                X4.octave = 3
                X5 = copy.deepcopy(notes[nn + 4])
                X5.octave = 3
                X6 = copy.deepcopy(notes[nn + 5])
                X6.octave = 3
                durata246 = X2.duration.quarterLength + X4.duration.quarterLength + X6.duration.quarterLength
                durata135 = X1.duration.quarterLength + X3.duration.quarterLength + X5.duration.quarterLength
                Cx = chord.Chord([X2, X4, X6])
                Cx.duration.quarterLength = durata246
                left.append(Cx)
                Cx = chord.Chord([X1, X3, X5])
                Cx.duration.quarterLength = durata135
                left.append(Cx)
                nn = nn + 6

        # bicordo finale: ultima nota una e due ottave sotto
        add_final_chord(left, notes, N)

        # pausa per completare l'ultima battuta
        fill_to_measure(left)

    # caso ternary
    elif seq_type == "Ternary":
        left = stream.Part()
        # check se inizia con pausa, perché proveniente da Retrograde
        for el in s.notesAndRests:
            if el.isRest:
                left.append(el)
            else:
                break

        notes = s.notes
        N = len(notes) - 1
        nn = 0

        if harmony_type == "classic":
            # accordi su tre note (una si una no dell'esacordo)
            while nn + 2 <= N:
                X1 = copy.deepcopy(notes[nn])
                X1.octave = 3
                X2 = copy.deepcopy(notes[nn+1])
                X2.octave = 3
                X3 = copy.deepcopy(notes[nn+2])
                X3.octave = 3
                durata = (X1.duration.quarterLength + X2.duration.quarterLength + X3.duration.quarterLength)
                Cx = chord.Chord([X1,X2,X3])
                Cx.duration.quarterLength = durata
                left.append(Cx)
                nn = nn+3
        elif harmony_type=="onbeat":
            while nn + 2 <= N:
                X1 = copy.deepcopy(notes[nn])
                X1.octave = 3
                X2 = copy.deepcopy(notes[nn+1])
                X2.octave = 3
                X3 = copy.deepcopy(notes[nn+2])
                X3.octave = 3
                durata = X1.duration.quarterLength
                Cx = chord.Chord([X1,X2])
                Cx.duration.quarterLength = durata
                left.append(Cx)
                # Pausa della durata di X2
                pausa = note.Rest()
                durata = X2.duration.quarterLength
                pausa.duration.quarterLength = durata
                left.append(pausa)
                Cx = chord.Chord([X2, X3])
                durata = X3.duration.quarterLength
                Cx.duration.quarterLength = durata
                left.append(Cx)

                nn = nn+3
        elif harmony_type=="offbeat":
            while nn + 2 <= N:
                X1 = copy.deepcopy(notes[nn])
                X1.octave = 3
                X2 = copy.deepcopy(notes[nn+1])
                X2.octave = 3
                X3 = copy.deepcopy(notes[nn+2])
                X3.octave = 3
                durata = X1.duration.quarterLength
                # Pausa della stessa durata
                pausa = note.Rest()
                pausa.duration.quarterLength = durata
                left.append(pausa)
                Cx = chord.Chord([X1,X2])
                durata = X2.duration.quarterLength
                Cx.duration.quarterLength = durata
                left.append(Cx)
                Cx = chord.Chord([X2, X3])
                durata = X3.duration.quarterLength
                Cx.duration.quarterLength = durata
                left.append(Cx)

                nn = nn+3
                
        # bicordo finale: ultima nota una e due ottave sotto
        add_final_chord(left, notes, N)

        # pausa per completare l'ultima battuta
        fill_to_measure(left)

    return left


def _make_chord_notes(bucket, indices):
    # Dato un bucket ordinato e una lista di indici, restituisce le note
    # all'ottava 3 pronte per costruire un accordo. Se risulta una sola nota,
    # la raddoppia un'ottava sotto.
    selected = [bucket[i] for i in indices if i < len(bucket)]
    chord_notes = []
    for n_ in selected:
        n_copy = copy.deepcopy(n_)
        n_copy.octave = 3
        chord_notes.append(n_copy)
    if len(chord_notes) == 1:
        low = copy.deepcopy(chord_notes[0])
        low.octave = 2
        chord_notes = [low, chord_notes[0]]
    return chord_notes


def genera_armonia_per_misura(s, harmony_type="classic", beats_per_measure=4):
    # Armonizzazione per length-constrained e free.
    # Per ogni misura di 4/4 le note vengono ordinate dal basso verso l'alto
    # e poi raggruppate in accordi secondo harmony_type:

    #   classic  – un accordo per battuta (4/4) con le note a indice pari (0,2,4,…)
    #   onbeat   – due accordi per battuta (2/4 ciascuno):
    #                1° accordo: note a indice pari  (0,2,4,…)
    #                2° accordo: note a indice dispari (1,3,5,…)
    #   offbeat  – due accordi per battuta (2/4 ciascuno):
    #                1° accordo: note a indice dispari (1,3,5,…)
    #                2° accordo: note a indice pari  (0,2,4,…)

    left = stream.Part()

    # raccoglie gli elementi con il loro offset cumulativo
    elements = list(s.flatten().notesAndRests)

    # numero di misure (arrotonda per eccesso)
    total_beats = sum(el.duration.quarterLength for el in elements)
    num_measures = int(total_beats // beats_per_measure)
    if total_beats % beats_per_measure > 0:
        num_measures += 1

    # bucket per misura
    buckets = [[] for _ in range(num_measures)]
    offset = 0.0
    for el in elements:
        if isinstance(el, note.Note):
            measure_idx = int(offset // beats_per_measure)
            if measure_idx < num_measures:
                buckets[measure_idx].append(copy.deepcopy(el))
        offset += el.duration.quarterLength

    for bucket in buckets:
        if not bucket:
            r = note.Rest()
            r.duration.quarterLength = beats_per_measure
            left.append(r)
            continue

        # ordina per altezza MIDI crescente
        bucket.sort(key=lambda n: n.pitch.midi)

        even_idx = list(range(0, len(bucket), 2))   # indici pari:   0,2,4,…
        odd_idx  = list(range(1, len(bucket), 2))   # indici dispari: 1,3,5,…

        if harmony_type == "classic":
            # un accordo intero per battuta, note a indici pari
            chord_notes = _make_chord_notes(bucket, even_idx)
            Cx = chord.Chord(chord_notes)
            Cx.duration.quarterLength = beats_per_measure
            left.append(Cx)

        elif harmony_type == "onbeat":
            # 1° metà: note pari  –  2° metà: note dispari
            even_notes = _make_chord_notes(bucket, even_idx)
            odd_notes  = _make_chord_notes(bucket, odd_idx) if odd_idx else _make_chord_notes(bucket, even_idx)
            C1 = chord.Chord(even_notes)
            C1.duration.quarterLength = beats_per_measure / 2
            left.append(C1)
            C2 = chord.Chord(odd_notes)
            C2.duration.quarterLength = beats_per_measure / 2
            left.append(C2)

        elif harmony_type == "offbeat":
            # 1° metà: note dispari (1,3,5,…)  –  2° metà: note pari (0,2,4,…)
            even_notes = _make_chord_notes(bucket, even_idx)
            odd_notes  = _make_chord_notes(bucket, odd_idx) if odd_idx else _make_chord_notes(bucket, even_idx)
            C1 = chord.Chord(odd_notes)
            C1.duration.quarterLength = beats_per_measure / 2
            left.append(C1)
            C2 = chord.Chord(even_notes)
            C2.duration.quarterLength = beats_per_measure / 2
            left.append(C2)

    return left
