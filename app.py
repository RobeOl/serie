from flask import Flask, send_file, request
from flask_cors import CORS
from music21 import *
import tempfile
import os
from sequenza import genera_sequenza
from armonia import genera_armonia

app = Flask(__name__)

CORS(app, origins=[
    "http://localhost:8000",
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
                   interval2=6, leap2=-2):

    s = genera_sequenza(sequence_type,tempo_type, note_length,
        interval,leap,
        interval1, leap1,
        interval2, leap2,
        ottave, bass_clef, start_note, harmony, harmony_type)

    if harmony and tempo_type=="sequence-constrained":
        left_hand = genera_armonia(sequence_type,tempo_type,s)
        # === Score (grand staff) ===
        melody = stream.Score()
        melody.insert(0, s)
        melody.insert(0, left_hand)
    else:
        melody = s
        melody.insert(0, key.Key('C'))
        melody.insert(0, metadata.Metadata())
        melody.metadata.title = ""
        melody.metadata.composer = ""

        melody.insert(0, instrument.Piano())

    return melody


# 🔹 FUNZIONE DI ACCESSO CON CACHE
def get_cached_stream(data):
    global last_stream, last_params, access_count

    # creiamo una chiave unica basata su TUTTI i parametri
    params = (
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
    )

    if (params != last_params) or (access_count > 1):
        last_stream = generate_music(*params)
        last_params = params
        access_count=1
    elif(access_count==2):
        last_stream = generate_music(*params)
        last_params = params
        access_count = 0
    else:
        access_count = 2

    return last_stream


@app.route("/generate", methods=["POST"])
def generate_midi():
    data = request.json

    s = get_cached_stream(data)

    tmp = tempfile.NamedTemporaryFile(suffix=".mid", delete=False)
    s.write('midi', fp=tmp.name)

    return send_file(tmp.name, mimetype="audio/midi")


@app.route("/score", methods=["POST"])
def generate_score():
    data = request.json

    s = get_cached_stream(data)

    tmp = tempfile.NamedTemporaryFile(suffix=".musicxml", delete=False)
    s.write('musicxml', fp=tmp.name)

    return send_file(tmp.name, mimetype="application/xml")

@app.route("/health")
def health():
    return {"status": "ok"}, 200


port = int(os.environ.get("PORT", 10000))
app.run(host="0.0.0.0", port=port)