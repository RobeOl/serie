import copy
from music21 import stream, note

# Range consentito: C3 (MIDI 48) – C6 (MIDI 84)
# MIDI_MIN = 48   # C3
# MIDI_MAX = 84   # C6
# MIDI_MIN = 60   # C4
# MIDI_MAX = 96   # C7
MIDI_MIN = 52   # E3
MIDI_MAX = 88   # E6


def centra_stream(s: stream.Part) -> stream.Part:
    # Prende un stream.Part (es. il risultato di invert_stream) e trasla
    # nota per nota verso l'alto o verso il basso di ottave intere (multipli
    # di 12 semitoni) in modo che ogni nota ricada nell'intervallo C3–C6
    # (MIDI 48–84).

    # Se lo span della melodia è contenibile in C3–C6, tutta la melodia viene
    # traslata di un unico shift globale (i rapporti di ottava tra le note
    # restano invariati).

    # Se lo span supera 36 semitoni (impossibile contenere in C3–C6 con un
    # solo shift), ogni singola nota viene corretta individualmente: viene
    # spostata di quante ottave servono per portarla dentro il range, senza
    # toccare le note già dentro.

    # --- raccoglie tutti i MIDI delle note (ignora pause) ---
    midi_pitches = [
        el.pitch.midi
        for el in s.recurse()
        if isinstance(el, note.Note)
    ]

    if not midi_pitches:
        centered = stream.Part()
        for el in s.recurse(classFilter=('Note', 'Rest')):
            centered.append(copy.deepcopy(el))
        return centered

    lowest  = min(midi_pitches)
    highest = max(midi_pitches)
    span    = highest - lowest

    centered = stream.Part()

    if span <= (MIDI_MAX - MIDI_MIN):
        shift = 0

        # Prima porta il centro della melodia nel range
        mid = (lowest + highest) // 2
        while mid + shift < MIDI_MIN:
            shift += 12
        while mid + shift > MIDI_MAX:
            shift -= 12

        # Poi aggiusta se lowest o highest sforano ancora
        while highest + shift > MIDI_MAX:
            shift -= 12
        while lowest + shift < MIDI_MIN:
            shift += 12

        for el in s.recurse(classFilter=('Note', 'Rest')):
            new_el = copy.deepcopy(el)
            if isinstance(new_el, note.Note):
                new_el.pitch.midi += shift
            centered.append(new_el)

    else:
        # ── CASO 2: correzione per nota ───────────────────────────────────
        # Lo span supera il range C3–C6: non è possibile un unico shift.
        # Ogni nota viene spostata individualmente di quante ottave servono
        # per portarla dentro [MIDI_MIN, MIDI_MAX].
        for el in s.recurse(classFilter=('Note', 'Rest')):
            new_el = copy.deepcopy(el)
            if isinstance(new_el, note.Note):
                m = new_el.pitch.midi
                while m < MIDI_MIN:
                    m += 12
                while m > MIDI_MAX:
                    m -= 12
                new_el.pitch.midi = m
            centered.append(new_el)

    return centered
