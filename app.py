from flask import Flask, send_file, request
from flask_cors import CORS
from music21 import *
import tempfile
import os
from multidimensional import genera_multidimensional

import copy
from centra import centra_stream

app = Flask(__name__)

CORS(app, origins=[
    "http://localhost:5002",
    "http://localhost:8000",
    "http://127.0.0.1:5002",
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

# def generate_music(start_note, tempo_type, bpm=100,
#                    note_length=1,
#                    k_value=None,
#                    multi_values=None):

#     s = genera_sequenza(tempo_type, note_length,
#         k_value, multi_values=multi_values)

    

#     melody = s
#     ts = meter.TimeSignature('4/4')
#     melody.insert(0, ts)
#     total_duration = melody.duration.quarterLength
#     measure_duration = ts.barDuration.quarterLength
#     remainder = total_duration % measure_duration
#     if remainder != 0:
#         missing = measure_duration - remainder
#         melody.append(note.Rest(quarterLength=missing))
#     melody.insert(0, key.Key('C'))
#     melody.insert(0, metadata.Metadata())
#     melody.metadata.title = ""
#     melody.metadata.composer = ""
#     melody.insert(0, instrument.Piano())

#     return melody

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
    # input_names = [el.nameWithOctave for el in s.flatten().notesAndRests if isinstance(el, note.Note)]
    # print("[retrograde_stream INPUT]", input_names)
 
    elements = list(s.flatten().notesAndRests)
 
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


@app.route("/multidimensional", methods=["POST"])
def generate_multidimensional():
    global last_stream, last_params

    data = request.json

    K             = int(data.get("k", 6))
    start_note    = int(data.get("start_note", 0))
    tempo_type    = data.get("tempo", "sequence-constrained")
    note_length   = float(data.get("note_length", 1))
    repeated      = bool(data.get("repeated", True))
    p_triplet     = float(data.get("p_triplet", 0.0))

    # Genera la sequenza
    melody = genera_multidimensional(tempo_type, note_length, K, start_note, repeated,
                                     p_triplet=p_triplet)

    # Aggiungi metadati e completa l'ultima battuta
    ts = meter.TimeSignature('4/4')
    melody.insert(0, ts)

    total    = melody.duration.quarterLength
    rem      = total % ts.barDuration.quarterLength
    if rem != 0:
        melody.append(note.Rest(quarterLength=ts.barDuration.quarterLength - rem))

    melody.insert(0, key.Key('C'))
    melody.insert(0, metadata.Metadata())
    melody.metadata.title = ""
    melody.metadata.composer = ""
    melody.insert(0, instrument.Piano())

    last_stream = copy.deepcopy(melody)
    last_params = data

    tmp = tempfile.NamedTemporaryFile(suffix=".mid", delete=False)
    melody.write('midi', fp=tmp.name)

    return send_file(tmp.name, mimetype="audio/midi")


# @app.route("/generate", methods=["POST"])
# def generate_midi():
#     global last_stream
#     global last_params

#     data = request.json

#     # Multidimensional: lista di K interi
#     raw_multi = data.get("multi_values", [])
#     multi_values = [int(v) for v in raw_multi] if raw_multi else None

#     s = generate_music(
#         data.get("start_note"),
#         data.get("sequence_type"),
#         data.get("tempo"),
#         data.get("harmony"),
#         data.get("harmony_type"),
#         data.get("octave", 1),
#         data.get("bass_clef"),
#         data.get("bpm", 100),
#         float(data.get("note_length", 1)),
#         data.get("interval", 0),
#         data.get("leap", 0),
#         data.get("interval1", 0),
#         data.get("leap1", 0),
#         data.get("interval2", 0),
#         data.get("leap2", 0),
#         data.get("int1", 0),
#         data.get("lea1", 0),
#         data.get("int2", 0),
#         data.get("lea2", 0),
#         data.get("int3", 0),
#         data.get("lea3", 0),
#         data.get("inter1", 0),
#         data.get("inter2", 0),
#         data.get("inter3", 0),
#         multi_values=multi_values
#     )

#     # salva la sequenza reale (fondamentale)
#     last_stream = copy.deepcopy(s)
#     # salva ultimi parametri
#     last_params = data

#     tmp = tempfile.NamedTemporaryFile(suffix=".mid", delete=False)
#     s.write('midi', fp=tmp.name)

#     return send_file(tmp.name, mimetype="audio/midi")


@app.route("/score", methods=["POST"])
def generate_score():
    global last_stream

    if last_stream is None:
        return {"error": "No sequence generated yet"}, 400

    tmp = tempfile.NamedTemporaryFile(suffix=".musicxml", delete=False)
    last_stream.write('musicxml', fp=tmp.name)

    return send_file(tmp.name, mimetype="application/xml")

@app.route("/import", methods=["POST"])
def import_midi():
    global last_stream, last_params

    if "midi" not in request.files:
        return {"error": "No MIDI file provided"}, 400

    f = request.files["midi"]

    # Salva il file MIDI in un temporaneo
    tmp_mid = tempfile.NamedTemporaryFile(suffix=".mid", delete=False)
    f.save(tmp_mid.name)

    # Carica con music21
    s = converter.parse(tmp_mid.name)

    # Rimuove indicazioni di tempo (metronomo) dal MIDI importato
    for el in s.recurse().getElementsByClass('MetronomeMark'):
        el.activeSite.remove(el)

    # Quantizza le durate per evitare valori float strani da DAW
    # (sui MIDI generati da GeCo non serve, ma è una protezione utile)
    s = s.quantize(quarterLengthDivisors=(4, 3))

    # Aggiunge metadati minimi se assenti
    if s.metadata is None:
        s.insert(0, metadata.Metadata())
        s.metadata.title = ""
        s.metadata.composer = ""
        s.insert(0, instrument.Piano())
    else:
        s.metadata.title = ""
        s.metadata.composer = ""

    # Aggiunge chiave di Do se assente
    if not s.flatten().getElementsByClass(key.Key):
        s.insert(0, key.Key('C'))

    # Salva come last_stream (le trasformazioni lavoreranno su questo)
    last_stream = copy.deepcopy(s)

    # last_params: legge i parametri passati dal frontend
    last_params = {
        "tempo": request.form.get("tempo", "constant"),
        "sequence_type": request.form.get("sequence_type", "Binary"),
        "harmony_type": request.form.get("harmony_type", "classic")
    }

    # Restituisce il MusicXML per OSMD (stesso percorso di /score)
    tmp_xml = tempfile.NamedTemporaryFile(suffix=".musicxml", delete=False)
    last_stream.write("musicxml", fp=tmp_xml.name)

    return send_file(tmp_xml.name, mimetype="application/xml")

@app.route("/transform", methods=["POST"])

def transform_sequence():
    global last_stream

    if last_stream is None:
        return {"error": "No sequence generated yet"}, 400

    data = request.json
    operation = data.get("operation")
    valore = data.get("value")

    if operation == "T":
        s = last_stream.transpose(valore)
    elif operation == "I":
        s = invert_stream(last_stream)
        s = centra_stream(s)
    elif operation=="R":
        s = retrograde_stream(last_stream)
    elif operation == "RI":
        s = retrograde_stream(invert_stream(last_stream))
        s = centra_stream(s)
    elif operation == "r_Sp":                
        flat = flatten_to_part(last_stream)  # ← appiattisci prima
        s = shift_part(flat)
    elif operation == "r_I":
        flat = flatten_to_part(last_stream)  # ← appiattisci prima
        s = invert_part_ranking(flat)
    elif operation == "r_R":
        flat = flatten_to_part(last_stream)  # ← appiattisci prima
        s = retrograde_rhythm_part(flat)
    elif operation == "r_Sm":
        flat = flatten_to_part(last_stream)  # ← appiattisci prima
        s = minus_shift_part(flat)
    else:
        return {"error": "Invalid operation"}, 400

    s.insert(0, key.Key('C'))
    s.insert(0, metadata.Metadata())
    s.insert(0, instrument.Piano())
    s.metadata.title = ""
    s.metadata.composer = ""
    last_stream = copy.deepcopy(s)

    # 🎵 esporta MIDI
    tmp = tempfile.NamedTemporaryFile(suffix=".mid", delete=False)
    s.write('midi', fp=tmp.name)

    return send_file(tmp.name, mimetype="audio/midi")

@app.route("/health")
def health():
    return {"status": "ok"}, 200


port = int(os.environ.get("PORT", 5002))
app.run(host="0.0.0.0", port=port)