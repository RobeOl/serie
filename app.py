from flask import Flask, send_file, request
from flask_cors import CORS
from music21 import *
import tempfile
import os
from sequenza import genera_sequenza
from armonia import genera_armonia, genera_armonia_per_misura, genera_armonia_coppie
import copy
from centra import centra_stream

app = Flask(__name__)

CORS(app, origins=[
    "http://localhost:5000",
    "http://localhost:8000",
    "http://127.0.0.1:5000",
    "null",  # ← per file aperti da file:// nel browser
    "https://murosigma.it",
    "https://www.murosigma.it",
    "https://marcobittelli.it",
    "https://www.marcobittelli.it"
])

# 🔹 CACHE GLOBALE
last_stream = None
last_params = None
access_count = 0

def generate_music(start_note, sequence_type, tempo_type, harmony, harmony_type, ottave, bass_clef, bpm=100,
                   note_length=1,
                   interval=3, leap=-1,
                   interval1=3, leap1=3,
                   interval2=6, leap2=-2,
                   int1=1,lea1=3,int2=-2,lea2=5,int3=3,lea3=-7,
                   inter1=3, inter2=3, inter3=6):

    s = genera_sequenza(sequence_type,tempo_type, note_length,
        interval,leap,
        interval1, leap1,
        interval2, leap2,
        int1, lea1, int2, lea2, int3, lea3,
        inter1,inter2,inter3,
        ottave, bass_clef, start_note, harmony, harmony_type)

    if harmony and (tempo_type in ("sequence-constrained", "constant", "length-constrained", "free")):
        if tempo_type in ("sequence-constrained", "constant"):
            left = genera_armonia(sequence_type, harmony_type, s)
        else:
            left = genera_armonia_coppie(s)
        # right hand
        right = stream.Part()
        for el in s:
            right.append(el)
        right.insert(0, instrument.Piano())
        ts = meter.TimeSignature('4/4')
        right.insert(0, ts)
        right.insert(0, clef.TrebleClef())
        # calcola lunghezza pausa rigo superiore
        total_duration = right.duration.quarterLength
        measure_duration = ts.barDuration.quarterLength
        remainder = total_duration % measure_duration
        if remainder != 0:
            missing = measure_duration - remainder
            right.append(note.Rest(quarterLength=missing))

        left.insert(0, instrument.Piano())
        left.insert(0, clef.BassClef())
        # calcola lunghezza pausa rigo inferiore
        total_duration = left.duration.quarterLength
        remainder = total_duration % measure_duration
        if remainder != 0:
            missing = measure_duration - remainder
            left.append(note.Rest(quarterLength=missing))

        # === Score (grand staff) ===
        melody = stream.Score()
        melody.insert(0, right)
        melody.insert(0, left)
        melody.insert(0, key.Key('C'))
        melody.insert(0, metadata.Metadata())
        melody.metadata.title = ""
        melody.metadata.composer = ""
        melody.insert(0, instrument.Piano())
    else:
        melody = s
        ts = meter.TimeSignature('4/4')
        melody.insert(0, ts)
        total_duration = melody.duration.quarterLength
        measure_duration = ts.barDuration.quarterLength
        remainder = total_duration % measure_duration
        if remainder != 0:
            missing = measure_duration - remainder
            melody.append(note.Rest(quarterLength=missing))
        melody.insert(0, key.Key('C'))
        melody.insert(0, metadata.Metadata())
        melody.metadata.title = ""
        melody.metadata.composer = ""
        melody.insert(0, instrument.Piano())

    return melody

def invert_stream(s):
    inverted = stream.Part()

    prev_pitch = None
    last_new_pitch = None

    for el in s.recurse():
        if isinstance(el, note.Note):
            if prev_pitch is None:
                new_note = note.Note(el.pitch, quarterLength=el.quarterLength)
                last_new_pitch = el.pitch.midi
            else:
                interval = el.pitch.midi - prev_pitch
                inv_interval = -interval
                new_pitch = last_new_pitch + inv_interval

                while abs(new_pitch - last_new_pitch) > 6:
                    if new_pitch < last_new_pitch:
                        new_pitch += 12
                    else:
                        new_pitch -= 12

                new_note = note.Note()
                new_note.pitch.midi = new_pitch
                new_note.quarterLength = el.quarterLength

                last_new_pitch = new_pitch

            prev_pitch = el.pitch.midi
            inverted.append(new_note)

        elif isinstance(el, note.Rest):
            inverted.append(note.Rest(quarterLength=el.quarterLength))

    return inverted

def retrograde_stream(s):
    new_stream = s.__class__()

    # # DEBUG input
    # input_names = [el.nameWithOctave for el in s.flat.notesAndRests if isinstance(el, note.Note)]
    # print("[retrograde_stream INPUT]", input_names)
 
    elements = list(s.flat.notesAndRests)
 
    if not elements:
        return new_stream
 
    # separa la pausa finale di riempimento (se presente)
    final_rest = None
    if isinstance(elements[-1], note.Rest):
        final_rest = elements[-1]
        elements = elements[:-1]
    
    # # escludi anche l'ultima nota (sempre uguale alla prima)
    # last_note = elements[-1]
    # elements = elements[:-1]
 
    # inverti ordine degli elementi musicali (senza la pausa finale)
    elements.reverse()
 
    offset = 0
    for el in elements:
        new_el = copy.deepcopy(el)
        new_stream.insert(offset, new_el)
        offset += new_el.duration.quarterLength

    #  # reinserisci l'ultima nota invariata
    # new_stream.insert(offset, copy.deepcopy(last_note))
    # offset += last_note.duration.quarterLength
 
    # riaggiungi la pausa finale invariata in coda
    if final_rest is not None:
        new_stream.insert(offset, copy.deepcopy(final_rest))

    # # DEBUG
    # output_names = [el.nameWithOctave for el in new_stream.recurse() if isinstance(el, note.Note)]
    # print("[retrograde_stream OUTPUT]", output_names)

    return new_stream


def flatten_to_part(s):
    # Riduce qualsiasi stream/part/score a una Part pulita con solo note e pause.
    flat = stream.Part()
    for el in s.flatten().notesAndRests:
        flat.append(copy.deepcopy(el))
    return flat

def shift_part(part):
    flat = stream.Part()
    for el in part.flatten().notesAndRests:
        flat.append(copy.deepcopy(el))

    elements = list(flat.notesAndRests)

    if not elements:
        return flat

    # separa ultima pausa se è finale
    last = elements[-1]
    final_rest = None

    if isinstance(last, note.Rest):
        final_rest = last
        core_elements = elements[:-1]
    else:
        core_elements = elements

    # escludi anche l'ultima nota (sempre uguale alla prima)
    last_note = core_elements[-1]
    core_elements = core_elements[:-1]

    if not core_elements:
        return flat

    # durate SOLO degli elementi musicali
    durations = [el.duration.quarterLength for el in core_elements]

    # shift circolare: la durata di ogni nota va alla successiva,
    # e la durata dell'ultima va alla prima
    # shift di 1
    #shifted_durations = [durations[-1]] + durations[:-1]

    # shift di 2
    shifted_durations = durations[-2:] + durations[:-2]
    
    # ricostruzione con i nuovi offset
    new_part = stream.Part()
    offset = 0

    for el, new_dur in zip(core_elements, shifted_durations):
        new_el = copy.deepcopy(el)
        new_el.duration.quarterLength = new_dur
        new_part.insert(offset, new_el)
        offset += new_dur

    # reinserisci l'ultima nota invariata
    new_part.insert(offset, copy.deepcopy(last_note))
    offset += last_note.duration.quarterLength

     # ricrea pausa finale corretta
    if final_rest is not None:
        new_part.insert(offset, copy.deepcopy(final_rest))

    return new_part

def minus_shift_part(part):
    flat = stream.Part()
    for el in part.flatten().notesAndRests:
        flat.append(copy.deepcopy(el))

    elements = list(flat.notesAndRests)

    if not elements:
        return flat

    # separa ultima pausa se è finale
    last = elements[-1]
    final_rest = None

    if isinstance(last, note.Rest):
        final_rest = last
        core_elements = elements[:-1]
    else:
        core_elements = elements

    # escludi anche l'ultima nota (sempre uguale alla prima)
    last_note = core_elements[-1]
    core_elements = core_elements[:-1]

    if not core_elements:
        return flat

    # durate SOLO degli elementi musicali
    durations = [el.duration.quarterLength for el in core_elements]

    # shift circolare: la durata di ogni nota va alla successiva,
    # e la durata dell'ultima va alla prima
    # shift di 1
    #shifted_durations = [durations[1]] + durations[:1]

    # shift di 2
    shifted_durations = durations[2:] + durations[:2]
    
    # ricostruzione con i nuovi offset
    new_part = stream.Part()
    offset = 0

    for el, new_dur in zip(core_elements, shifted_durations):
        new_el = copy.deepcopy(el)
        new_el.duration.quarterLength = new_dur
        new_part.insert(offset, new_el)
        offset += new_dur

    # reinserisci l'ultima nota invariata
    new_part.insert(offset, copy.deepcopy(last_note))
    offset += last_note.duration.quarterLength

     # ricrea pausa finale corretta
    if final_rest is not None:
        new_part.insert(offset, copy.deepcopy(final_rest))

    return new_part

def fill_to_measure(seq, beats_per_measure=4):
    # Aggiunge una pausa finale per completare l'ultima battuta.
    total = sum(el.duration.quarterLength for el in seq.notesAndRests)
    position_in_measure = total % beats_per_measure
    if position_in_measure > 0:
        remainder = beats_per_measure - position_in_measure
        r = note.Rest()
        r.duration.quarterLength = remainder
        seq.append(r)

# inversione ritmica
def invert_part_ranking(part):
    flat = stream.Part()
    for el in part.flatten().notesAndRests:
        flat.append(copy.deepcopy(el))

    elements = list(flat.notesAndRests)

    if not elements:
        return flat

    # separa ultima pausa se è finale
    last = elements[-1]
    final_rest = None

    if isinstance(last, note.Rest):
        final_rest = last
        core_elements = elements[:-1]
    else:
        core_elements = elements

    if not core_elements:
        return flat

    # durate SOLO degli elementi musicali
    durations = [el.duration.quarterLength for el in core_elements]

    # escludi anche l'ultima nota (sempre uguale alla prima)
    last_note = core_elements[-1]
    core_elements = core_elements[:-1]
    durations = durations[:-1]

    if not core_elements:
        return flat

    sorted_unique = sorted(set(durations))
    rank_map = {d: i for i, d in enumerate(sorted_unique)}
    max_rank = len(sorted_unique) - 1

    inverted_map = {
        d: sorted_unique[max_rank - rank_map[d]]
        for d in sorted_unique
    }

    # ricostruzione con nuovi offset
    new_part = stream.Part()
    offset = 0

    for el in core_elements:
        new_el = copy.deepcopy(el)
        d = new_el.duration.quarterLength
        new_el.duration.quarterLength = inverted_map[d]
        new_part.insert(offset, new_el)
        offset += new_el.duration.quarterLength

    # reinserisci l'ultima nota invariata
    new_part.insert(offset, copy.deepcopy(last_note))
    offset += last_note.duration.quarterLength

    # ricrea pausa finale
    # if final_rest is not None:
    #     new_part.insert(offset, copy.deepcopy(final_rest))

    # pausa per completare l'ultima battuta
    fill_to_measure(new_part)

    return new_part


def retrograde_rhythm_part(part):
    flat = stream.Part()
    for el in part.flatten().notesAndRests:
        flat.append(copy.deepcopy(el))

    elements = list(flat.notesAndRests)

    if not elements:
        return flat

    # separa ultima pausa finale
    last = elements[-1]
    final_rest = None

    if isinstance(last, note.Rest):
        final_rest = last
        core_elements = elements[:-1]
    else:
        core_elements = elements

    if not core_elements:
        return flat

    # escludi anche l'ultima nota (sempre uguale alla prima)
    last_note = core_elements[-1]
    core_elements = core_elements[:-1]

    if not core_elements:
        return flat

    # retrogradazione: inversione dell'ordine delle durate
    durations = [el.duration.quarterLength for el in core_elements]
    durations.reverse()

    # ricostruzione
    new_part = stream.Part()
    offset = 0

    for el, new_dur in zip(core_elements, durations):
        new_el = copy.deepcopy(el)
        new_el.duration.quarterLength = new_dur
        new_part.insert(offset, new_el)
        offset += new_dur

    # reinserisci l'ultima nota invariata
    new_part.insert(offset, copy.deepcopy(last_note))
    offset += last_note.duration.quarterLength

    # ricrea pausa finale
    if final_rest is not None:
        new_part.insert(offset, copy.deepcopy(final_rest))

    return new_part


@app.route("/generate", methods=["POST"])
def generate_midi():
    global last_stream
    global last_params

    data = request.json

    s = generate_music(
        data.get("start_note"),
        data.get("sequence_type"),
        data.get("tempo"),
        data.get("harmony"),
        data.get("harmony_type"),
        data.get("octave", 1),
        data.get("bass_clef"),
        data.get("bpm", 100),
        float(data.get("note_length", 1)),
        data.get("interval", 0),
        data.get("leap", 0),
        data.get("interval1", 0),
        data.get("leap1", 0),
        data.get("interval2", 0),
        data.get("leap2", 0),
        data.get("int1", 0),
        data.get("lea1", 0),
        data.get("int2", 0),
        data.get("lea2", 0),
        data.get("int3", 0),
        data.get("lea3", 0),
        data.get("inter1", 0),
        data.get("inter2", 0),
        data.get("inter3", 0)
    )

    # salva la sequenza reale (fondamentale)
    last_stream = copy.deepcopy(s)
    # salva ultimi parametri
    last_params = data

    tmp = tempfile.NamedTemporaryFile(suffix=".mid", delete=False)
    s.write('midi', fp=tmp.name)

    return send_file(tmp.name, mimetype="audio/midi")


@app.route("/score", methods=["POST"])
def generate_score():
    global last_stream

    if last_stream is None:
        return {"error": "No sequence generated yet"}, 400

    tmp = tempfile.NamedTemporaryFile(suffix=".musicxml", delete=False)
    last_stream.write('musicxml', fp=tmp.name)

    return send_file(tmp.name, mimetype="application/xml")

def rigenera_armonia(melody):
    tempo_type = last_params.get("tempo")
    if tempo_type in ("sequence-constrained", "constant"):
        return genera_armonia(
            last_params.get("sequence_type"),
            last_params.get("harmony_type"),
            melody
        )
    else:
        return genera_armonia_coppie(melody)

@app.route("/transform", methods=["POST"])

def transform_sequence():
    global last_stream

    if last_stream is None:
        return {"error": "No sequence generated yet"}, 400

    data = request.json
    operation = data.get("operation")
    valore = data.get("value")

    if operation == "T":
        # 🎼 CASO CON ARMONIA
        if isinstance(last_stream, stream.Score):

            parts = list(last_stream.parts)

            right = parts[0]  # melodia

            # 1. trasponi melodia
            transposed_melody = right.transpose(valore)

            # 2. rigenera armonia
            new_left = rigenera_armonia(transposed_melody)
            
            # 3. ricostruisci score
            new_score = stream.Score()

            # mano destra
            new_score.insert(0, transposed_melody)
            # added 02 may
            new_score.insert(0, clef.TrebleClef())

            # mano sinistra
            #new_left.insert(0, instrument.Piano())
            new_left.insert(0, clef.BassClef())
            new_score.insert(0, new_left)

            # metadata
            #new_score.insert(0, key.Key('C'))
            new_score.insert(0, metadata.Metadata())
            #new_score.insert(0, instrument.Piano())
            new_score.metadata.title = ""
            new_score.metadata.composer = ""

            last_stream = copy.deepcopy(new_score)

            s = new_score

        # 🎼 CASO SENZA ARMONIA
        else:
            s = last_stream.transpose(valore)
            s.insert(0, key.Key('C'))
            s.insert(0, metadata.Metadata())
            s.insert(0, instrument.Piano())
            s.metadata.title = ""
            s.metadata.composer = ""
            last_stream = copy.deepcopy(s)
    elif operation == "I":
        # 🎼 CASO CON ARMONIA
        if isinstance(last_stream, stream.Score):

            parts = list(last_stream.parts)

            right = parts[0]  # melodia

            # 1. inverti melodia
            inverted_melody = invert_stream(right)
            inverted_melody = centra_stream(inverted_melody)
            inverted_melody.clef = clef.TrebleClef()

            # 2. rigenera armonia
            new_left = rigenera_armonia(inverted_melody)
            
            # 3. ricostruisci score
            new_score = stream.Score()

            # mano destra
            new_score.insert(0, inverted_melody)

            # mano sinistra
            #new_left.insert(0, instrument.Piano())
            new_left.insert(0, clef.BassClef())
            new_score.insert(0, new_left)

            # metadata
            #new_score.insert(0, key.Key('C'))
            new_score.insert(0, metadata.Metadata())
            #new_score.insert(0, instrument.Piano())
            new_score.metadata.title = ""
            new_score.metadata.composer = ""

            last_stream = copy.deepcopy(new_score)

            s = new_score

        # 🎼 CASO SENZA ARMONIA
        else:
            s = invert_stream(last_stream)
            s = centra_stream(s)
            s.insert(0, key.Key('C'))
            s.insert(0, metadata.Metadata())
            s.insert(0, instrument.Piano())
            s.metadata.title = ""
            s.metadata.composer = ""
            last_stream = copy.deepcopy(s)
    elif operation=="R":
        # 🎼 CASO CON ARMONIA
        if isinstance(last_stream, stream.Score):
 
            parts = list(last_stream.parts)
 
            right = parts[0]  # melodia
 
            # 1. retrogrado melodia
            retro_melody = retrograde_stream(right)
            retro_melody.clef = clef.TrebleClef()
 
            # 2. rigenera armonia
            new_left = rigenera_armonia(retro_melody)
            
            # 3. ricostruisci score
            new_score = stream.Score()
 
            # mano destra
            new_score.insert(0, retro_melody)
 
            # mano sinistra
            #new_left.insert(0, instrument.Piano())
            new_left.insert(0, clef.BassClef())
            new_score.insert(0, new_left)
 
            # metadata
            #new_score.insert(0, key.Key('C'))
            new_score.insert(0, metadata.Metadata())
            #new_score.insert(0, instrument.Piano())
            new_score.metadata.title = ""
            new_score.metadata.composer = ""
 
            last_stream = copy.deepcopy(new_score)
 
            s = new_score
 
        # 🎼 CASO SENZA ARMONIA
        else:
            s = retrograde_stream(last_stream)
            s.insert(0, key.Key('C'))
            s.insert(0, metadata.Metadata())
            s.insert(0, instrument.Piano())
            s.metadata.title = ""
            s.metadata.composer = ""
            last_stream = copy.deepcopy(s)

    elif operation == "RI":
        # 🎼 CASO CON ARMONIA
        if isinstance(last_stream, stream.Score):

            parts = list(last_stream.parts)
            right = parts[0]  # melodia

            # 👇 QUI va la tua riga
            retro_inverted = retrograde_stream(invert_stream(right))
            retro_inverted = centra_stream(retro_inverted)
            retro_inverted.clef = clef.TrebleClef()

            # rigenera armonia
            new_left = rigenera_armonia(retro_inverted)

            # ricostruzione score
            new_score = stream.Score()
            new_score.insert(0, retro_inverted)

            #new_left.insert(0, instrument.Piano())
            new_left.insert(0, clef.BassClef())
            new_score.insert(0, new_left)

            new_score.insert(0, key.Key('C'))
            new_score.insert(0, metadata.Metadata())
            #new_score.insert(0, instrument.Piano())
            new_score.metadata.title = ""
            new_score.metadata.composer = ""

            last_stream = copy.deepcopy(new_score)
            s = new_score

        else:
            # 👇 stesso punto anche qui
            s = retrograde_stream(invert_stream(last_stream))
            s = centra_stream(s)

            s.insert(0, key.Key('C'))
            s.insert(0, metadata.Metadata())
            s.insert(0, instrument.Piano())
            s.metadata.title = ""
            s.metadata.composer = ""

            last_stream = copy.deepcopy(s)
    elif operation == "r_Sp":
        # 🎼 CASO CON ARMONIA
        if isinstance(last_stream, stream.Score):

            parts = list(last_stream.parts)
            right = flatten_to_part(parts[0])  # ← appiattisci prima
            # right = parts[0]  # melodia

            # 1. shift ritmico melodia di uno step avanti
            shifted_melody = shift_part(right)
            shifted_melody.clef = clef.TrebleClef() 

            # 2. rigenera armonia
            new_left = rigenera_armonia(shifted_melody)
            
            # 3. ricostruisci score
            new_score = stream.Score()

            # mano destra
            new_score.insert(0, shifted_melody)

            # mano sinistra
            #new_left.insert(0, instrument.Piano())
            new_left.insert(0, clef.BassClef())
            new_score.insert(0, new_left)

            # metadata
            #new_score.insert(0, key.Key('C'))
            new_score.insert(0, metadata.Metadata())
            #new_score.insert(0, instrument.Piano())
            new_score.metadata.title = ""
            new_score.metadata.composer = ""

            last_stream = copy.deepcopy(new_score)  # ← manca
            s = new_score 

        # 🎼 CASO SENZA ARMONIA
        else:
            flat = flatten_to_part(last_stream)  # ← appiattisci prima
            s = shift_part(flat)
            s.insert(0, key.Key('C'))
            s.insert(0, metadata.Metadata())
            s.insert(0, instrument.Piano())
            s.metadata.title = ""
            s.metadata.composer = ""
            last_stream = copy.deepcopy(s)
    elif operation == "r_I":
        # 🎼 CASO CON ARMONIA
        if isinstance(last_stream, stream.Score):

            parts = list(last_stream.parts)
            right = flatten_to_part(parts[0])  # ← appiattisci prima
            # right = parts[0]  # melodia

            # 1. inverti melodia
            inverted_melody = invert_part_ranking(right)
            inverted_melody.clef = clef.TrebleClef()

            # 2. rigenera armonia
            new_left = rigenera_armonia(inverted_melody)
            
            # 3. ricostruisci score
            new_score = stream.Score()

            # mano destra
            new_score.insert(0, inverted_melody)

            # mano sinistra
            #new_left.insert(0, instrument.Piano())
            new_left.insert(0, clef.BassClef())
            new_score.insert(0, new_left)

            # metadata
            #new_score.insert(0, key.Key('C'))
            new_score.insert(0, metadata.Metadata())
            #new_score.insert(0, instrument.Piano())
            new_score.metadata.title = ""
            new_score.metadata.composer = ""

            last_stream = copy.deepcopy(new_score)  # ← manca
            s = new_score 

        # 🎼 CASO SENZA ARMONIA
        else:
            flat = flatten_to_part(last_stream)  # ← appiattisci prima
            s = invert_part_ranking(flat)
            s.insert(0, key.Key('C'))
            s.insert(0, metadata.Metadata())
            s.insert(0, instrument.Piano())
            s.metadata.title = ""
            s.metadata.composer = ""
            last_stream = copy.deepcopy(s)
    elif operation == "r_R":
        # 🎼 CASO CON ARMONIA
        if isinstance(last_stream, stream.Score):

            parts = list(last_stream.parts)
            right = flatten_to_part(parts[0])  # ← appiattisci prima
            # right = parts[0]  # melodia

            # 1. inverti melodia
            r_retro_melody = retrograde_rhythm_part(right)
            r_retro_melody.clef = clef.TrebleClef()

            # 2. rigenera armonia
            new_left = rigenera_armonia(r_retro_melody)
            
            # 3. ricostruisci score
            new_score = stream.Score()

            # mano destra
            new_score.insert(0, r_retro_melody)

            # mano sinistra
            #new_left.insert(0, instrument.Piano())
            new_left.insert(0, clef.BassClef())
            new_score.insert(0, new_left)

            # metadata
            #new_score.insert(0, key.Key('C'))
            new_score.insert(0, metadata.Metadata())
            #new_score.insert(0, instrument.Piano())
            new_score.metadata.title = ""
            new_score.metadata.composer = ""

            last_stream = copy.deepcopy(new_score)  # ← manca
            s = new_score 

        # 🎼 CASO SENZA ARMONIA
        else:
            flat = flatten_to_part(last_stream)  # ← appiattisci prima
            s = retrograde_rhythm_part(flat)
            s.insert(0, key.Key('C'))
            s.insert(0, metadata.Metadata())
            s.insert(0, instrument.Piano())
            s.metadata.title = ""
            s.metadata.composer = ""
            last_stream = copy.deepcopy(s)
    elif operation == "r_Sm":
        # 🎼 CASO CON ARMONIA
        if isinstance(last_stream, stream.Score):

            parts = list(last_stream.parts)
            right = flatten_to_part(parts[0])  # ← appiattisci prima
            
            # 1. permuta ritmi melodia
            shifted_melody = minus_shift_part(right)
            shifted_melody.clef = clef.TrebleClef()

            # 2. rigenera armonia
            new_left = rigenera_armonia(shifted_melody)
            
            # 3. ricostruisci score
            new_score = stream.Score()

            # mano destra
            new_score.insert(0, shifted_melody)

            # mano sinistra
            #new_left.insert(0, instrument.Piano())
            new_left.insert(0, clef.BassClef())
            new_score.insert(0, new_left)

            # metadata
            #new_score.insert(0, key.Key('C'))
            new_score.insert(0, metadata.Metadata())
            #new_score.insert(0, instrument.Piano())
            new_score.metadata.title = ""
            new_score.metadata.composer = ""

            last_stream = copy.deepcopy(new_score)  # ← manca
            s = new_score 

        # 🎼 CASO SENZA ARMONIA
        else:
            flat = flatten_to_part(last_stream)  # ← appiattisci prima
            s = minus_shift_part(flat)
            s.insert(0, key.Key('C'))
            s.insert(0, metadata.Metadata())
            s.insert(0, instrument.Piano())
            s.metadata.title = ""
            s.metadata.composer = ""
            last_stream = copy.deepcopy(s)
    else:
        return {"error": "Invalid operation"}, 400

    # 🎵 esporta MIDI
    tmp = tempfile.NamedTemporaryFile(suffix=".mid", delete=False)
    s.write('midi', fp=tmp.name)

    return send_file(tmp.name, mimetype="audio/midi")

@app.route("/health")
def health():
    return {"status": "ok"}, 200


port = int(os.environ.get("PORT", 5000))
app.run(host="0.0.0.0", port=port)