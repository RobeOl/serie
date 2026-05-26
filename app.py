# ════════════════════════════════════════════════════════════════════════════
#  app.py  —  Backend Flask per GeCo-Tool con autenticazione JWT
#
#  Endpoint:
#    POST /auth/login   → verifica email + codice, restituisce token JWT
#    POST /auth/log     → logga ogni accesso all'app (richiede token)
#    GET  /admin/users  → lista utenti e log (richiede header X-Admin-Key)
#    POST /generate     → genera MIDI (richiede token JWT valido)
#    POST /score        → restituisce MusicXML (richiede token JWT valido)
#    GET  /health       → check disponibilità server
#
#  Dipendenze:  flask  flask-cors  music21  PyJWT
#
#  File di dati (nella stessa cartella di app.py):
#    users.json       → lista utenti autorizzati (gestito manualmente da te)
#    access_log.json  → log degli accessi (generato automaticamente)
# ════════════════════════════════════════════════════════════════════════════

from flask import Flask, send_file, request, jsonify
from flask_cors import CORS
from music21 import stream, note, clef, meter, key, metadata, instrument
from functools import wraps
import tempfile
import copy
import json
import os
import jwt
import datetime

from binary import genera_binary

# ── Configurazione ───────────────────────────────────────────────────────────

# CAMBIA QUESTI VALORI prima del deploy!
JWT_SECRET    = os.environ.get("JWT_SECRET",    "cambia_questa_stringa_segreta_123")
ADMIN_KEY     = os.environ.get("ADMIN_KEY",     "cambia_questa_chiave_admin_456")
JWT_EXP_HOURS = int(os.environ.get("JWT_EXP_HOURS", 24))   # durata token in ore

# Percorsi dei file dati (relativi alla cartella di app.py)
BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
USERS_FILE    = os.path.join(BASE_DIR, "users.json")
LOG_FILE      = os.path.join(BASE_DIR, "access_log.json")

# ── Stato globale ────────────────────────────────────────────────────────────
last_stream = None

# ── Inizializzazione Flask ───────────────────────────────────────────────────
app = Flask(__name__)

CORS(app,
    origins=[
        "http://localhost:5000",
        "http://localhost:8000",
        "http://127.0.0.1:5000",
        "null",
        "https://murosigma.it",
        "https://www.murosigma.it",
        "https://marcobittelli.it",
        "https://www.marcobittelli.it"
    ],
    methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Admin-Key"],
    supports_credentials=True
)


# ════════════════════════════════════════════════════════════════════════════
#  HELPERS: lettura/scrittura file JSON
# ════════════════════════════════════════════════════════════════════════════

def load_users():
    """Legge users.json. Se non esiste restituisce lista vuota."""
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_log():
    """Legge access_log.json. Se non esiste restituisce lista vuota."""
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def append_log(entry: dict):
    """Aggiunge una voce al log degli accessi (append sicuro)."""
    log = load_log()
    log.append(entry)
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)


# ════════════════════════════════════════════════════════════════════════════
#  DECORATOR: require_token
#  Protegge gli endpoint che richiedono autenticazione JWT.
#  Il token va inviato nell'header:  Authorization: Bearer <token>
# ════════════════════════════════════════════════════════════════════════════

def require_token(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Token mancante"}), 401
        token = auth_header.split(" ", 1)[1]
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            request.user_email = payload.get("email", "unknown")
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token scaduto, effettua di nuovo il login"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Token non valido"}), 401
        return f(*args, **kwargs)
    return decorated


# ════════════════════════════════════════════════════════════════════════════
#  ENDPOINT: POST /auth/login
#
#  Body JSON: { "email": "...", "code": "..." }
#  Risposta:  { "token": "<jwt>" }   oppure  401
# ════════════════════════════════════════════════════════════════════════════

@app.route("/auth/login", methods=["POST"])
def login():
    data  = request.json or {}
    email = (data.get("email") or "").strip().lower()
    code  = (data.get("code")  or "").strip()

    if not email or not code:
        return jsonify({"error": "Email e codice obbligatori"}), 400

    users = load_users()
    user  = next(
        (u for u in users
         if u["email"].lower() == email and u["code"] == code and u.get("active", True)),
        None
    )

    if not user:
        # Log tentativo fallito
        append_log({
            "type":      "login_failed",
            "email":     email,
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "ip":        request.headers.get("X-Forwarded-For", request.remote_addr)
        })
        return jsonify({"error": "Credenziali non valide o accesso non autorizzato"}), 401

    # Genera token JWT
    payload = {
        "email": email,
        "exp":   datetime.datetime.utcnow() + datetime.timedelta(hours=JWT_EXP_HOURS)
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")

    # Log login riuscito
    append_log({
        "type":      "login_ok",
        "email":     email,
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "ip":        request.headers.get("X-Forwarded-For", request.remote_addr)
    })

    return jsonify({"token": token}), 200


# ════════════════════════════════════════════════════════════════════════════
#  ENDPOINT: POST /auth/log
#
#  Il frontend chiama questo endpoint ogni volta che l'utente usa l'app
#  (es. ogni Generate). Richiede token valido.
#  Body JSON: { "action": "generate" }  (opzionale, per dettaglio)
# ════════════════════════════════════════════════════════════════════════════

@app.route("/auth/log", methods=["POST"])
@require_token
def log_access():
    data   = request.json or {}
    action = data.get("action", "app_use")
    append_log({
        "type":      action,
        "email":     request.user_email,
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "ip":        request.headers.get("X-Forwarded-For", request.remote_addr)
    })
    return jsonify({"ok": True}), 200


# ════════════════════════════════════════════════════════════════════════════
#  ENDPOINT: GET /admin/users
#
#  Restituisce la lista utenti e il log degli accessi.
#  Protetto da header:  X-Admin-Key: <ADMIN_KEY>
#  Solo per uso tuo (non esporre nell'interfaccia pubblica).
# ════════════════════════════════════════════════════════════════════════════

@app.route("/admin/users", methods=["GET"])
def admin_users():
    if request.headers.get("X-Admin-Key") != ADMIN_KEY:
        return jsonify({"error": "Non autorizzato"}), 403

    users = load_users()
    log   = load_log()

    # Statistiche rapide per utente
    from collections import Counter
    logins  = [e["email"] for e in log if e.get("type") == "login_ok"]
    actions = [e["email"] for e in log if e.get("type") == "generate"]
    login_counts  = Counter(logins)
    action_counts = Counter(actions)

    summary = []
    for u in users:
        em = u["email"].lower()
        summary.append({
            "email":       u["email"],
            "active":      u.get("active", True),
            "logins":      login_counts.get(em, 0),
            "generations": action_counts.get(em, 0),
        })

    return jsonify({
        "users":  summary,
        "log":    log[-100:]   # ultime 100 voci
    }), 200


# ════════════════════════════════════════════════════════════════════════════
#  FUNZIONE: build_score
# ════════════════════════════════════════════════════════════════════════════

def build_score(melody):
    ts = meter.TimeSignature('4/4')
    melody.insert(0, ts)
    total     = melody.duration.quarterLength
    remainder = total % ts.barDuration.quarterLength
    if remainder != 0:
        melody.append(note.Rest(quarterLength=ts.barDuration.quarterLength - remainder))
    melody.insert(0, key.Key('C'))
    melody.insert(0, instrument.Piano())
    melody.insert(0, metadata.Metadata())
    melody.metadata.title    = ""
    melody.metadata.composer = ""
    return melody


# ════════════════════════════════════════════════════════════════════════════
#  ENDPOINT: POST /generate  (protetto da token)
# ════════════════════════════════════════════════════════════════════════════

@app.route("/generate", methods=["POST"])
@require_token
def generate_midi():
    global last_stream
    data = request.json

    start_note   = data.get("start_note",   0)
    interval     = data.get("interval",     3)
    leap         = data.get("leap",        -1)
    tempo        = data.get("tempo",        "constant")
    note_length  = float(data.get("note_length", 0.5))
    ottave       = data.get("octave",       2)
    bass_clef    = data.get("bass_clef",    False)
    harmony      = data.get("harmony",      False)
    harmony_type = data.get("harmony_type", None)

    melody = genera_binary(
        tempo, note_length, interval, leap,
        ottave, bass_clef, start_note, harmony, harmony_type
    )
    score = build_score(melody)

    tmp = tempfile.NamedTemporaryFile(suffix=".mid", delete=False)
    score.write('midi', fp=tmp.name)
    last_stream = copy.deepcopy(score)

    # Log dell'azione
    append_log({
        "type":      "generate",
        "email":     request.user_email,
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "params":    {"interval": interval, "leap": leap}
    })

    return send_file(tmp.name, mimetype="audio/midi")


# ════════════════════════════════════════════════════════════════════════════
#  ENDPOINT: POST /score  (protetto da token)
# ════════════════════════════════════════════════════════════════════════════

@app.route("/score", methods=["POST"])
@require_token
def generate_score():
    if last_stream is None:
        return {"error": "No sequence generated yet"}, 400
    tmp = tempfile.NamedTemporaryFile(suffix=".musicxml", delete=False)
    last_stream.write('musicxml', fp=tmp.name)
    return send_file(tmp.name, mimetype="application/xml")


# ════════════════════════════════════════════════════════════════════════════
#  ENDPOINT: GET /health
# ════════════════════════════════════════════════════════════════════════════

@app.route("/health")
def health():
    return {"status": "ok"}, 200


# ── Avvio ────────────────────────────────────────────────────────────────────
port = int(os.environ.get("PORT", 5000))
app.run(host="0.0.0.0", port=port)
