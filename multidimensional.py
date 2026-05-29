from music21 import *
import random
import copy
from utility import f_durata


def genera_multidimensional(tipo, note_len, K, starting_note, repeated=True):
    """
    Genera una sequenza di K note casuali.

    Parametri
    ---------
    tipo          : str   – "sequence-constrained" | "length-constrained" |
                            "constant" | "free"
    note_len      : float – durata nota (solo in modalità "constant")
    K             : int   – numero di note da generare (2–12)
    starting_note : int   – pitch-class 0-11 (0=C, 1=C#, …, 11=B)
    repeated      : bool  – True → note ripetibili, False → tutte diverse
    """

    if K < 2:
        K = 2

    # ── pool di altezze: 1 ottava cromatica a partire da starting_note ──────
    # Convention music21: MIDI = 12 * (octave + 1) + pitch_class
    # C4 = 12*5 + 0 = 60,  G3 = 12*4 + 7 = 55
    base_octave = 4 if starting_note <= 6 else 3
    base_midi   = 12 * (base_octave + 1) + starting_note  # es. C4=60, G3=55

    # Il pool è l'ottava cromatica che parte da base_midi (senza % 128)
    pool_midi = [base_midi + i for i in range(12)]

    # ── scelta delle note ────────────────────────────────────────────────────
    # La prima nota è sempre la starting_note; le restanti K-1 sono casuali
    if repeated:
        chosen_midi = [base_midi] + [random.choice(pool_midi) for _ in range(K - 1)]
    else:
        # le K-1 note successive devono essere diverse tra loro e dalla prima
        remaining_pool = [m for m in pool_midi if m != base_midi]
        chosen_midi = [base_midi] + random.sample(remaining_pool, min(K - 1, len(remaining_pool)))

    # ── costruzione della lista note con durate ──────────────────────────────
    notes = []

    if tipo == "constant":
        for m in chosen_midi:
            n = note.Note()
            n.pitch.midi = m
            n.duration.quarterLength = note_len
            notes.append(n)

    elif tipo == "free":
        for m in chosen_midi:
            n = note.Note()
            n.pitch.midi = m
            f_durata(n)
            notes.append(n)

    elif tipo == "sequence-constrained":
        # cambio di durata ogni K note (una volta per "ciclo")
        current_dur = random.choice([1, 0.5, 0.25])
        for i, m in enumerate(chosen_midi):
            n = note.Note()
            n.pitch.midi = m
            if i % K == 0:
                current_dur = random.choice([1, 0.5, 0.25])
            n.duration.quarterLength = current_dur
            notes.append(n)

    else:  # length-constrained
        note_number = random.choice([2, 3, 5, 6])
        conta = 0
        current_dur = random.choice([1, 0.5, 0.25])
        for m in chosen_midi:
            n = note.Note()
            n.pitch.midi = m
            if conta == note_number:
                current_dur = random.choice([1, 0.5, 0.25])
                conta = 0
            n.duration.quarterLength = current_dur
            conta += 1
            notes.append(n)

    # ── costruzione stream ───────────────────────────────────────────────────
    melody = stream.Part()
    for n in notes:
        melody.append(n)

    return melody
