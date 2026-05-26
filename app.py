# ════════════════════════════════════════════════════════════════════════════
#  app.py  —  Backend Flask per GeCo-Tool con autenticazione e logging
#
#  Endpoint pubblici:
#    POST /register      → registra email, crea codice in attesa
#    POST /verify        → verifica codice, restituisce JWT
#    GET  /health        → check disponibilità server
#
#  Endpoint protetti (richiedono JWT valido):
#    POST /generate      → genera sequenza MIDI
#    POST /score         → restituisce MusicXML
#
#  Endpoint admin (richiedono header X-Admin-Key):
#    GET  /admin/users   → lista utenti registrati
#    GET  /admin/stats   → accessi per utente e per endpoint
#    POST /admin/activate  → attiva un utente fornendo il codice
#    DELETE /admin/user  → elimina un utente
#
#  Dipendenze:  flask  flask-cors  music21  PyJWT
#  Installa con:  pip install flask flask-cors music21 PyJWT
# ════════════════════════════════════════════════════════════════════════════

import os
import sqlite3
import secrets
import copy
import tempfile
import datetime

from flask import Flask, send_file, request, jsonify, g
from flask_cors import CORS
from music21 import stream, note, clef, meter, key, metadata, instrument
import jwt

from binary import genera_binary


# ── Configurazione ───────────────────────────────────────────────────────────

# Cambia queste due costanti nelle variabili d'ambiente di Render:
#   JWT_SECRET  → stringa casuale lunga (es. genera con: python -c "import secrets; print(secrets.token_hex(32))")
#   ADMIN_KEY   → password per accedere agli endpoint /admin/*
JWT_SECRET = os.environ.get("JWT_SECRET", "cambia-questo-segreto-in-produzione")
ADMIN_KEY  = os.environ.get("ADMIN_KEY",  "admin-password-da-cambiare")
JWT_EXP_DAYS = 30   # il token JWT scade dopo N giorni

DB_PATH = os.environ.get("DB_PATH", "geco.db")


# ── Stato globale ────────────────────────────────────────────────────────────
last_stream = None

# ── Inizializzazione Flask ───────────────────────────────────────────────────
app = Flask(__name__)

CORS(app, origins=[
    "http://localhost:5000",
    "http://localhost:8000",
    "http://127.0.0.1:5000",
    "null",
    "https://murosigma.it",
    "https://www.murosigma.it",
    "https://marcobittelli.it",
    "https://www.marcobittelli.it"
])


# ════════════════════════════════════════════════════════════════════════════
#  DATABASE  (SQLite — file locale, persiste sul disco di Render se si usa
#  un Persistent Disk; altrimenti si azzera ad ogni deploy → valuta PostgreSQL
#  per produzione seria)
# ════════════════════════════════════════════════════════════════════════════

def get_db():
    """Restituisce la connessione SQLite per la richiesta corrente."""
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db:
        db.close()

def init_db():
    """Crea le tabelle se non esistono."""
    with app.app_context():
        db = get_db()
        db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                email      TEXT    NOT NULL UNIQUE,
                code       TEXT    NOT NULL,
                active     INTEGER NOT NULL DEFAULT 0,   -- 0 = in attesa, 1 = attivato
                created_at TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS access_log (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                email      TEXT    NOT NULL,
                endpoint   TEXT    NOT NULL,
                ts         TEXT    NOT NULL
            );
        """)
        db.commit()

init_db()


# ════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ════════════════════════════════════════════════════════════════════════════

def require_auth(f):
    """
    Decoratore: verifica il token JWT nell'header Authorization.
    Inietta request.user_email se valido, altrimenti restituisce 401.
    """
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({"error": "Token mancante"}), 401
        token = auth[7:]
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token scaduto"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Token non valido"}), 401

        # Controlla che l'utente sia ancora attivo nel DB
        db = get_db()
        user = db.execute("SELECT active FROM users WHERE email=?", (payload["email"],)).fetchone()
        if not user or not user["active"]:
            return jsonify({"error": "Utente non autorizzato"}), 403

        request.user_email = payload["email"]
        return f(*args, **kwargs)
    return decorated


def require_admin(f):
    """Decoratore: verifica l'header X-Admin-Key."""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.headers.get("X-Admin-Key") != ADMIN_KEY:
            return jsonify({"error": "Non autorizzato"}), 403
        return f(*args, **kwargs)
    return decorated


def log_access(email, endpoint):
    """Scrive una riga nella tabella access_log."""
    db = get_db()
    db.execute(
        "INSERT INTO access_log (email, endpoint, ts) VALUES (?, ?, ?)",
        (email, endpoint, datetime.datetime.utcnow().isoformat())
    )
    db.commit()


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
#  ENDPOINT PUBBLICI
# ════════════════════════════════════════════════════════════════════════════

@app.route("/register", methods=["POST"])
def register():
    """
    Riceve {"email": "..."}.
    Crea il record utente con un codice casuale a 8 caratteri.
    L'utente NON è ancora attivo: devi attivarlo via /admin/activate.
    Restituisce il codice così che tu possa inviarlo manualmente all'utente.
    """
    data  = request.json or {}
    email = (data.get("email") or "").strip().lower()
    if not email or "@" not in email:
        return jsonify({"error": "Email non valida"}), 400

    db   = get_db()
    existing = db.execute("SELECT id, active FROM users WHERE email=?", (email,)).fetchone()

    if existing:
        if existing["active"]:
            return jsonify({"error": "Email già registrata e attiva"}), 409
        else:
            # Rigenera il codice se era in attesa
            code = secrets.token_hex(4).upper()   # es. "A3F7B2C1"
            db.execute("UPDATE users SET code=? WHERE email=?", (code, email))
            db.commit()
            return jsonify({
                "message": "Registrazione aggiornata. In attesa di attivazione.",
                "code":    code   # mostrato solo in questa risposta — salvalo tu
            }), 200

    code = secrets.token_hex(4).upper()
    db.execute(
        "INSERT INTO users (email, code, active, created_at) VALUES (?, ?, 0, ?)",
        (email, code, datetime.datetime.utcnow().isoformat())
    )
    db.commit()

    # Il codice viene restituito nella risposta JSON (visibile solo a te via curl/Postman)
    # In alternativa puoi integrare un servizio email (SendGrid, Mailgun, ecc.)
    return jsonify({
        "message": "Registrazione ricevuta. In attesa di attivazione da parte dell'amministratore.",
        "code":    code   # ← invia questo codice all'utente via email manualmente
    }), 201


@app.route("/verify", methods=["POST"])
def verify():
    """
    Riceve {"email": "...", "code": "..."}.
    Se email+codice sono corretti e l'utente è attivo → restituisce JWT.
    """
    data  = request.json or {}
    email = (data.get("email") or "").strip().lower()
    code  = (data.get("code")  or "").strip().upper()

    if not email or not code:
        return jsonify({"error": "Email e codice sono obbligatori"}), 400

    db   = get_db()
    user = db.execute(
        "SELECT active, code FROM users WHERE email=?", (email,)
    ).fetchone()

    if not user:
        return jsonify({"error": "Email non trovata"}), 404
    if user["code"] != code:
        return jsonify({"error": "Codice non corretto"}), 401
    if not user["active"]:
        return jsonify({"error": "Account non ancora attivato. Attendi la conferma."}), 403

    # Genera il JWT
    payload = {
        "email": email,
        "exp":   datetime.datetime.utcnow() + datetime.timedelta(days=JWT_EXP_DAYS)
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")

    log_access(email, "verify/login")
    return jsonify({"token": token}), 200


@app.route("/health")
def health():
    return {"status": "ok"}, 200


# ════════════════════════════════════════════════════════════════════════════
#  ENDPOINT PROTETTI  (richiedono JWT valido)
# ════════════════════════════════════════════════════════════════════════════

@app.route("/generate", methods=["POST"])
@require_auth
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
    log_access(request.user_email, "generate")
    return send_file(tmp.name, mimetype="audio/midi")


@app.route("/score", methods=["POST"])
@require_auth
def generate_score():
    if last_stream is None:
        return {"error": "No sequence generated yet"}, 400
    tmp = tempfile.NamedTemporaryFile(suffix=".musicxml", delete=False)
    last_stream.write('musicxml', fp=tmp.name)
    log_access(request.user_email, "score")
    return send_file(tmp.name, mimetype="application/xml")


# ════════════════════════════════════════════════════════════════════════════
#  ENDPOINT ADMIN  (richiedono header X-Admin-Key: <ADMIN_KEY>)
# ════════════════════════════════════════════════════════════════════════════

@app.route("/admin/users", methods=["GET"])
@require_admin
def admin_users():
    """Lista tutti gli utenti registrati."""
    db    = get_db()
    users = db.execute(
        "SELECT id, email, code, active, created_at FROM users ORDER BY created_at DESC"
    ).fetchall()
    return jsonify([dict(u) for u in users]), 200


@app.route("/admin/activate", methods=["POST"])
@require_admin
def admin_activate():
    """
    Attiva un utente: {"email": "..."}.
    Da chiamare dopo aver ricevuto la registrazione e aver inviato il codice.
    """
    data  = request.json or {}
    email = (data.get("email") or "").strip().lower()
    db    = get_db()
    user  = db.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
    if not user:
        return jsonify({"error": "Utente non trovato"}), 404
    db.execute("UPDATE users SET active=1 WHERE email=?", (email,))
    db.commit()
    return jsonify({"message": f"Utente {email} attivato"}), 200


@app.route("/admin/deactivate", methods=["POST"])
@require_admin
def admin_deactivate():
    """Disattiva un utente (revoca accesso senza eliminarlo)."""
    data  = request.json or {}
    email = (data.get("email") or "").strip().lower()
    db    = get_db()
    db.execute("UPDATE users SET active=0 WHERE email=?", (email,))
    db.commit()
    return jsonify({"message": f"Utente {email} disattivato"}), 200


@app.route("/admin/user", methods=["DELETE"])
@require_admin
def admin_delete_user():
    """Elimina un utente: {"email": "..."}."""
    data  = request.json or {}
    email = (data.get("email") or "").strip().lower()
    db    = get_db()
    db.execute("DELETE FROM users WHERE email=?", (email,))
    db.execute("DELETE FROM access_log WHERE email=?", (email,))
    db.commit()
    return jsonify({"message": f"Utente {email} eliminato"}), 200


@app.route("/admin/stats", methods=["GET"])
@require_admin
def admin_stats():
    """
    Restituisce:
      - totale accessi per utente
      - dettaglio accessi per endpoint
      - ultimi 50 accessi cronologici
    """
    db = get_db()

    per_user = db.execute("""
        SELECT email, COUNT(*) as total
        FROM access_log
        GROUP BY email
        ORDER BY total DESC
    """).fetchall()

    per_endpoint = db.execute("""
        SELECT email, endpoint, COUNT(*) as count
        FROM access_log
        GROUP BY email, endpoint
        ORDER BY email, count DESC
    """).fetchall()

    recent = db.execute("""
        SELECT email, endpoint, ts
        FROM access_log
        ORDER BY ts DESC
        LIMIT 50
    """).fetchall()

    return jsonify({
        "per_user":     [dict(r) for r in per_user],
        "per_endpoint": [dict(r) for r in per_endpoint],
        "recent":       [dict(r) for r in recent],
    }), 200


# ── Avvio ────────────────────────────────────────────────────────────────────
port = int(os.environ.get("PORT", 5000))
app.run(host="0.0.0.0", port=port)
