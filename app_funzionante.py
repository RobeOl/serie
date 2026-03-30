from flask import Flask, send_file, request
from flask_cors import CORS
from music21 import *
import tempfile
import os
from binary import genera_binary
from quaternary import genera_quaternary

app = Flask(__name__)

CORS(app, origins=[
    "http://localhost:8000",
    "https://murosigma.it"
])

# 🔹 CACHE GLOBALE
last_stream = None
last_params = None
access_count = 0


def generate_music(start_note, sequence_type, tempo_type, harmony,
                   note_length=1,
                   interval=3, leap=-1,
                   interval1=3, leap1=3,
                   interval2=6, leap2=-2):

    if sequence_type == "Binary":
        s = genera_binary(tempo_type, note_length, interval, leap, start_note)
    else:
        s = genera_quaternary(tempo_type, note_length,
                              interval1, leap1,
                              interval2, leap2,
                              start_note)

    s.insert(0, metadata.Metadata())
    s.metadata.title = ""
    s.metadata.composer = ""

    s.insert(0, instrument.Piano())

    return s


# 🔹 FUNZIONE DI ACCESSO CON CACHE
def get_cached_stream(data):
    global last_stream, last_params, access_count

    # creiamo una chiave unica basata su TUTTI i parametri
    params = (
        data.get("start_note"),
        data.get("sequence_type"),
        data.get("tempo"),
        data.get("harmony"),
        float(data.get("note_length", 1)),
        data.get("interval", 0),
        data.get("leap", 0),
        data.get("interval1", 0),
        data.get("leap1", 0),
        data.get("interval2", 0),
        data.get("leap2", 0),
    )

    # se i parametri cambiano → rigenera
    # if params != last_params:
    #     last_stream = generate_music(*params)
    #     last_params = params
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


port = int(os.environ.get("PORT", 10000))
app.run(host="0.0.0.0", port=port)