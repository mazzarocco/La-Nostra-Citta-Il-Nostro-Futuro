import os
import datetime
from functools import wraps
from flask import Flask, request, jsonify
import mysql.connector
from mysql.connector import Error
import jwt
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from flask_cors import CORS

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})
app.config['SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'chiave_segreta_default')
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


@app.route('/', methods=['GET'])
def index():
    return jsonify({
        'messaggio': 'API La Nostra Città attiva',
        'endpoints': [
            '/api/login',
            '/api/registrazione',
            '/api/segnalazioni',
            '/api/segnalazioni/<id_segnalazione>/sostieni'
        ]
    }), 200

DB_CONFIG = {
    'host': os.environ.get('DB_HOST', '127.0.0.1'),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', ''),
    'database': os.environ.get('DB_NAME', 'la_nostra_citta')
}

def get_db_connection():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Error as e:
        print(f"Errore DB: {e}")
        return None

# --- DECORATORE AUTH ---
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(" ")[1]
        if not token:
            return jsonify({'errore': 'Token mancante'}), 401
        try:
            current_user = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        except:
            return jsonify({'errore': 'Token non valido o scaduto'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

# --- 1. REGISTRAZIONE ---
@app.route('/api/registrazione', methods=['POST'])
def registrazione():
    data = request.json
    nome, cognome, email, pwd = data.get('nome'), data.get('cognome'), data.get('email'), data.get('password')
    if not all([nome, cognome, email, pwd]):
        return jsonify({"errore": "Dati mancanti"}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({"errore": "Database non disponibile"}), 503

    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO utente (nome, cognome, email, password) VALUES (%s, %s, %s, %s)",
                   (nome, cognome, email, pwd))
        conn.commit()
        return jsonify({"messaggio": "Registrato!"}), 201
    except mysql.connector.IntegrityError:
        return jsonify({"errore": "Email già in uso"}), 409
    finally:
        cursor.close()
        conn.close()

# --- 2. LOGIN ---
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email, pwd = data.get('email'), data.get('password')
    conn = get_db_connection()
    if conn is None:
        return jsonify({"errore": "Database non disponibile"}), 503

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id_utente, password, ruolo, stato_account FROM utente WHERE email = %s", (email,))
        utente = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()

    if utente and utente['stato_account'] == 'ATTIVO' and pwd == utente['password']:
        token = jwt.encode({'id_utente': utente['id_utente'], 'ruolo': utente['ruolo'],
                            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)},
                           app.config['SECRET_KEY'], algorithm="HS256")
        return jsonify({"token": token, "ruolo": utente['ruolo']}), 200
    return jsonify({"errore": "Credenziali errate o account inattivo"}), 401

# --- 3. INSERIMENTO SEGNALAZIONE ---
@app.route('/api/segnalazioni', methods=['POST'])
@token_required
def crea_segnalazione(current_user):
    titolo, descrizione, id_quartiere = request.form.get('titolo'), request.form.get('descrizione'), request.form.get('id_quartiere')
    if 'allegato' not in request.files or not all([titolo, descrizione, id_quartiere]):
        return jsonify({"errore": "Dati o allegato mancanti"}), 400

    file = request.files['allegato']
    nome_file = secure_filename(file.filename)
    percorso = os.path.join(app.config['UPLOAD_FOLDER'], nome_file)
    file.save(percorso)

    conn = get_db_connection()
    if conn is None:
        return jsonify({"errore": "Database non disponibile"}), 503

    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO segnalazione (titolo, descrizione, id_autore, id_quartiere, id_stato_corrente) VALUES (%s, %s, %s, %s, 1)",
                       (titolo, descrizione, current_user['id_utente'], id_quartiere))
        id_seg = cursor.lastrowid
        cursor.execute("INSERT INTO allegato (nome_file, percorso_file, tipo_mime, tipo_media, dimensione_bytes, id_segnalazione) VALUES (%s, %s, %s, %s, %s, %s)",
                       (nome_file, percorso, file.mimetype, 'IMMAGINE' if 'image' in file.mimetype else 'VIDEO', os.path.getsize(percorso), id_seg))
        conn.commit()
        return jsonify({"id_segnalazione": id_seg}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"errore": str(e)}), 400
    finally:
        cursor.close()
        conn.close()

# --- 4. LETTURA SEGNALAZIONI PUBBLICHE ---
@app.route('/api/segnalazioni', methods=['GET'])
def get_segnalazioni():
    conn = get_db_connection()
    if conn is None:
        return jsonify({"errore": "Database non disponibile"}), 503

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM v_segnalazioni_pubbliche")
        risultati = cursor.fetchall()
        return jsonify(risultati), 200
    finally:
        cursor.close()
        conn.close()

# --- 5. SOSTEGNO SEGNALAZIONE ---
@app.route('/api/segnalazioni/<int:id_segnalazione>/sostieni', methods=['POST'])
@token_required
def sostieni(current_user, id_segnalazione):
    conn = get_db_connection()
    if conn is None:
        return jsonify({"errore": "Database non disponibile"}), 503

    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO sostegno (id_utente, id_segnalazione) VALUES (%s, %s)",
                       (current_user['id_utente'], id_segnalazione))
        conn.commit()
        return jsonify({"messaggio": "Sostegno aggiunto!"}), 201
    except mysql.connector.Error:
        return jsonify({"errore": "Impossibile sostenere questa segnalazione (forse è la tua o hai già votato)."}), 400
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(debug=True, port=5000)