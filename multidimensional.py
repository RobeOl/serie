from music21 import *
import random
import copy
from utility import f_durata

BEATS_PER_MEASURE = 4.0

def genera_multidimensional(tipo, note_len, K, starting_note, repeated=True,
                             p_triplet=0.0):
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
    p_triplet     : float – [0.0–1.0] probabilità che una coppia di note
                            (solo in modalità "constant") diventi una terzina.
                            0.0 = mai, 1.0 = sempre (se possibile).
    """

    if K < 2:
        K = 2

    # ── pool di altezze ──────────────────────────────────────────────────────
    base_octave = 4 if starting_note <= 6 else 3
    base_midi   = 12 * (base_octave + 1) + starting_note
    pool_midi   = [base_midi + i for i in range(12)]

    # ── scelta delle note ────────────────────────────────────────────────────
    if repeated:
        chosen_midi = [base_midi] + [random.choice(pool_midi) for _ in range(K - 1)]
    else:
        remaining_pool = [m for m in pool_midi if m != base_midi]
        chosen_midi = [base_midi] + random.sample(remaining_pool, min(K - 1, len(remaining_pool)))

    # ── costruzione della lista note con durate ──────────────────────────────
    notes = []

    if tipo == "constant":
        normal_type    = duration.quarterLengthToClosestType(note_len)[0]
        triplet_note_ql = note_len * 2 / 3  # durata reale di ogni nota nella terzina
        triplet_span    = note_len * 2       # spazio totale occupato dalla terzina (= 2 note_len)

        # ── Fase 1: decidi il layout in gruppi ────────────────────────────────
        # Scandisce chosen_midi a coppie: ogni coppia viene assegnata
        # a "triplet" o "pair" (due note singole).
        # Una coppia con indice dispari residua diventa nota singola.
        # Il vincolo di battuta viene verificato SUL GRUPPO, non sulla nota.
        groups = []   # lista di dict: {"type": "triplet"|"single", "midi": [...]}
        position = 0.0
        i = 0
        while i < len(chosen_midi):
            pos_in_measure = position % BEATS_PER_MEASURE
            space_left     = BEATS_PER_MEASURE - pos_in_measure

            pair_available  = i + 1 < len(chosen_midi)
            fits_in_measure = triplet_span <= space_left + 1e-9

            if pair_available and fits_in_measure and random.random() < p_triplet:
                # terzina: consuma coppia (i, i+1) + nota extra casuale
                m3 = random.choice(pool_midi)
                groups.append({"type": "triplet",
                               "midi": [chosen_midi[i], chosen_midi[i+1], m3]})
                position += triplet_span
                i += 2
            elif pair_available and fits_in_measure:
                # coppia normale: due note singole consecutive
                groups.append({"type": "pair",
                               "midi": [chosen_midi[i], chosen_midi[i+1]]})
                position += note_len * 2
                i += 2
            else:
                # nota singola (ultima dispari, o coppia non entra in battuta)
                groups.append({"type": "single",
                               "midi": [chosen_midi[i]]})
                position += note_len
                i += 1

        # ── Fase 2: costruisci le note dai gruppi ────────────────────────────
        for g in groups:
            if g["type"] == "triplet":
                for m in g["midi"]:
                    n = note.Note()
                    n.pitch.midi = m
                    n.duration = duration.Duration(triplet_note_ql)  # durata reale 2/3 del valore base
                    t = duration.Tuplet(numberNotesActual=3, numberNotesNormal=2)
                    t.durationNormal = duration.DurationTuple(
                        type=normal_type, dots=0, quarterLength=note_len  # riferimento al valore base
                    )
                    n.duration.appendTuplet(t)
                    notes.append(n)
            else:
                # "pair" o "single": note normali
                for m in g["midi"]:
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
        conta       = 0
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
