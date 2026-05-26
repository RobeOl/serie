# ════════════════════════════════════════════════════════════════════════════
#  binary.py  —  Generazione della sequenza binaria (versione didattica)
#
#  Espone una sola funzione pubblica:
#    genera_binary(tipo, note_len, i, j, ottave, bass_clef,
#                  starting_note, harmony, harmony_type)
#
#  In questa versione minimale viene mantenuto solo il ramo "constant"
#  (tutte le note hanno la stessa durata), che è l'unico usato dal frontend
#  ridotto.
#
#  Dipendenze:  music21,  utility.py (f_octave)
# ════════════════════════════════════════════════════════════════════════════

from music21 import stream, note, clef
import copy

# f_octave: corregge l'ottava di una nota se esce dal range consentito.
# È definita in utility.py e condivisa con gli altri moduli del progetto.
# from utility import f_octave


# ════════════════════════════════════════════════════════════════════════════
#  FUNZIONE: genera_binary
#
#  Costruisce la sequenza binaria come lista di oggetti note.Note di music21,
#  poi la restituisce come stream.Stream.
#
#  ALGORITMO (ramo "constant"):
#    1. Parte dalla nota iniziale (starting_note) con ottava assegnata
#       automaticamente (C–F# → ottava 4, G–B → ottava 3).
#    2. Aggiunge la nota corrente alla lista.
#    3. La traspone di `i` semitoni (Interval) → aggiunge il risultato.
#    4. La traspone di `j` semitoni (Leap) → questa è la prima nota
#       del ciclo successivo. Registra la coppia (prima, seconda).
#    5. Ripete i passi 3–4 finché la coppia corrente non torna uguale
#       alla prima coppia (chiusura modulare).
#    6. Rimuove l'ultima nota (duplicato della prima) e restituisce lo stream.
#
#  PARAMETRI:
#    tipo          : str    tipo di ritmo; solo "constant" è usato qui
#    note_len      : float  durata in quarti di ogni nota (es. 0.25 = sedicesimo)
#    i             : int    Interval in semitoni (positivo=su, negativo=giù)
#    j             : int    Leap in semitoni
#    ottave        : int    range in ottave (1 = compatto, 2 = esteso)
#    bass_clef     : bool   se True, traspone la melodia -24 semitoni
#                           e inserisce la chiave di basso
#    starting_note : int    classe di altezza iniziale (0=Do … 11=Si)
#    harmony       : bool   non usato in questa versione (sempre False)
#    harmony_type  : str    non usato in questa versione
#
#  RESTITUISCE:
#    stream.Stream  con le note della sequenza
# ════════════════════════════════════════════════════════════════════════════
def genera_binary(tipo, note_len, i, j, ottave, bass_clef,
                  starting_note, harmony, harmony_type):

    # ── Nota iniziale ────────────────────────────────────────────────────────
    # music21 accetta un intero MIDI come pitch: 60 = C4.
    # starting_note è una pitch-class (0–11); l'ottava viene scelta
    # in modo che la melodia parta in un registro comodo per il pianoforte.
    c = note.Note(starting_note)
    c.octave = 4 if starting_note <= 6 else 3   # C–F# → oct4, G–B → oct3
    oct = c.octave   # ottava di riferimento per f_octave

    notes = []       # lista delle note da inserire nello stream
    note1 = c        # puntatore alla nota corrente (viene modificata in-place)

    # ── Ramo "constant": tutte le note hanno la stessa durata ────────────────
    # quarterLength esprime la durata in quarti di semibreve:
    #   1.0 = quarto,  0.5 = ottavo,  0.25 = sedicesimo, ecc.
    note1.duration.quarterLength = note_len

    # Prima nota (la nota iniziale)
    notes.append(copy.deepcopy(note1))
    prima = note1.name           # nome della pitch-class, es. "C", "F#"

    # Prima trasposizione: applica Interval
    note1.transpose(i, inPlace=True)
    # f_octave(note1, ottave, oct)   # riporta nel range se necessario
    notes.append(copy.deepcopy(note1))
    seconda = note1.name

    # Registra la prima coppia: sarà la condizione di stop del ciclo
    first_couple = [prima, seconda]

    # ── Ciclo principale ─────────────────────────────────────────────────────
    # Continua finché la coppia corrente non torna uguale alla prima.
    # Questo garantisce la chiusura modulare della sequenza.
    condition = True
    while condition:

        # Applica Leap: salto di collegamento fra un ciclo e il successivo
        note1.transpose(j, inPlace=True)
        # f_octave(note1, ottave, oct)
        notes.append(copy.deepcopy(note1))
        prima = note1.name

        # Applica Interval: passo interno al nuovo ciclo
        note1.transpose(i, inPlace=True)
        # f_octave(note1, ottave, oct)
        notes.append(copy.deepcopy(note1))
        seconda = note1.name

        current_couple = [prima, seconda]

        # La sequenza si chiude quando ritroviamo la stessa coppia iniziale
        condition = (current_couple != first_couple)

    # ── Costruzione dello stream ─────────────────────────────────────────────
    melody = stream.Stream()

    # L'ultima nota è sempre uguale alla prima (chiusura del ciclo):
    # la rimuoviamo per evitare la ripetizione.
    notes.pop()

    # ── Chiave di basso (opzionale) ──────────────────────────────────────────
    # Se richiesto, la melodia viene trasposta due ottave in basso (-24 semitoni)
    # e notata in chiave di basso, utile per studi per violoncello, fagotto, ecc.
    if bass_clef:
        melody.insert(0, clef.BassClef())
        melody.append(notes)
        melody = melody.transpose(-24)
    else:
        melody.append(notes)

    return melody
