import os
import datetime
import uuid
from functools import wraps
from flask import Flask, request, jsonify
import boto3
import mysql.connector
from mysql.connector import Error
import jwt
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from flask_cors import CORS

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})
IS_PRODUCTION = os.environ.get('APP_ENV', '').lower() == 'production' or os.environ.get('VERCEL') == '1'
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
if IS_PRODUCTION and not JWT_SECRET_KEY:
    raise RuntimeError('JWT_SECRET_KEY e obbligatoria in produzione')
app.config['SECRET_KEY'] = JWT_SECRET_KEY or 'chiave_segreta_solo_sviluppo'

STORAGE_BUCKET = os.environ.get('STORAGE_BUCKET')
STORAGE_ENDPOINT_URL = os.environ.get('STORAGE_ENDPOINT_URL')
STORAGE_REGION = os.environ.get('STORAGE_REGION', 'us-east-1')
STORAGE_ACCESS_KEY_ID = os.environ.get('STORAGE_ACCESS_KEY_ID')
STORAGE_SECRET_ACCESS_KEY = os.environ.get('STORAGE_SECRET_ACCESS_KEY')
STORAGE_CONFIGURED = all((
    STORAGE_BUCKET,
    STORAGE_ACCESS_KEY_ID,
    STORAGE_SECRET_ACCESS_KEY,
))
if IS_PRODUCTION and not STORAGE_CONFIGURED:
    raise RuntimeError(
        'Storage privato non configurato: servono STORAGE_BUCKET, '
        'STORAGE_ACCESS_KEY_ID e STORAGE_SECRET_ACCESS_KEY'
    )

storage_client = None
if STORAGE_CONFIGURED:
    storage_client = boto3.client(
        's3',
        endpoint_url=STORAGE_ENDPOINT_URL or None,
        region_name=STORAGE_REGION,
        aws_access_key_id=STORAGE_ACCESS_KEY_ID,
        aws_secret_access_key=STORAGE_SECRET_ACCESS_KEY,
    )


def upload_private_file(file_storage, folder, object_name=None):
    """Upload a file to a private bucket and return its object key and size."""
    if storage_client is None or not STORAGE_BUCKET:
        raise RuntimeError('Storage privato non configurato')

    original_name = secure_filename(file_storage.filename or '')
    extension = os.path.splitext(original_name)[1].lower()
    object_name = object_name or f'{uuid.uuid4().hex}{extension}'
    object_key = f'{folder}/{object_name}'
    file_storage.stream.seek(0, os.SEEK_END)
    file_size = file_storage.stream.tell()
    file_storage.stream.seek(0)
    storage_client.upload_fileobj(
        file_storage.stream,
        STORAGE_BUCKET,
        object_key,
        ExtraArgs={'ContentType': file_storage.mimetype or 'application/octet-stream'},
    )
    return object_key, file_size


def delete_private_files(object_keys):
    if storage_client is None or not STORAGE_BUCKET:
        return
    for object_key in object_keys:
        try:
            storage_client.delete_object(Bucket=STORAGE_BUCKET, Key=object_key)
        except Exception as error:
            app.logger.warning("Impossibile eliminare l'oggetto storage %s: %s", object_key, error)


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
    'port': int(os.environ.get('DB_PORT', '3306')),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', ''),
    'database': os.environ.get('DB_NAME', 'la_nostra_citta')
}

if os.environ.get('DB_SSL_CA'):
    DB_CONFIG['ssl_ca'] = os.environ['DB_SSL_CA']
elif os.environ.get('DB_SSL_CA_CONTENT'):
    db_ssl_ca_path = '/tmp/aiven-ca.pem'
    with open(db_ssl_ca_path, 'w', encoding='utf-8') as certificate_file:
        certificate_file.write(os.environ['DB_SSL_CA_CONTENT'])
    DB_CONFIG['ssl_ca'] = db_ssl_ca_path

def get_db_connection():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Error as e:
        print(f"Errore DB: {e}")
        return None

def registra_attivita(conn, id_utente, azione, entita=None, id_entita=None, dettagli=None):
    cursor = conn.cursor()
    try:
        try:
            cursor.execute(
                """INSERT INTO log_attivita (id_utente, azione, entita, id_entita, dettagli)
                   VALUES (%s, %s, %s, %s, %s)""",
                (id_utente, azione, entita, id_entita, dettagli)
            )
        except Error:
            # L'audit non deve annullare l'operazione principale durante un aggiornamento dello schema.
            conn.rollback()
    finally:
        cursor.close()

# --- DECORATORE AUTH ---
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.removeprefix('Bearer ').strip()
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
    data = request.form
    nome = data.get('nome', '').strip()
    cognome = data.get('cognome', '').strip()
    email = data.get('email', '').strip().lower()
    codice_fiscale = data.get('codice_fiscale', '').strip().upper()
    indirizzo = data.get('indirizzo_residenza', '').strip()
    data_nascita = data.get('data_nascita', '').strip()
    pwd = data.get('password', '')
    fronte = request.files.get('documento_fronte')
    retro = request.files.get('documento_retro')

    if not all([nome, cognome, email, codice_fiscale, indirizzo, data_nascita, pwd, fronte, retro]):
        return jsonify({"errore": "Tutti i dati e i documenti sono obbligatori"}), 400
    try:
        nascita = datetime.date.fromisoformat(data_nascita)
    except ValueError:
        return jsonify({"errore": "Data di nascita non valida"}), 400
    oggi = datetime.date.today()
    eta = oggi.year - nascita.year - ((oggi.month, oggi.day) < (nascita.month, nascita.day))
    if nascita > oggi or eta < 18:
        return jsonify({"errore": "Per registrarti devi essere maggiorenne"}), 400
    if fronte.mimetype not in {'image/jpeg', 'image/png', 'image/webp'} or retro.mimetype not in {'image/jpeg', 'image/png', 'image/webp'}:
        return jsonify({"errore": "I documenti devono essere immagini JPG, PNG o WEBP"}), 400
    if storage_client is None:
        return jsonify({"errore": "Storage documenti non configurato"}), 503

    nomi_documenti = []
    try:
        for documento in (fronte, retro):
            nome_file, _ = upload_private_file(documento, 'documenti-identita')
            nomi_documenti.append(nome_file)
    except Exception:
        delete_private_files(nomi_documenti)
        return jsonify({"errore": "Salvataggio dei documenti non riuscito"}), 503

    conn = get_db_connection()
    if conn is None:
        delete_private_files(nomi_documenti)
        return jsonify({"errore": "Database non disponibile"}), 503

    cursor = conn.cursor()
    try:
        cursor.execute("""INSERT INTO utente
            (nome, cognome, email, codice_fiscale, indirizzo_residenza, data_nascita,
             password, documento_fronte, documento_retro, stato_account)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'IN_VERIFICA')""",
            (nome, cognome, email, codice_fiscale, indirizzo, nascita,
             generate_password_hash(pwd), nomi_documenti[0], nomi_documenti[1]))
        conn.commit()
        registra_attivita(conn, cursor.lastrowid, 'REGISTRAZIONE')
        conn.commit()
        return jsonify({"messaggio": "Registrazione completata. Attendi la verifica dell'account."}), 201
    except mysql.connector.IntegrityError:
        delete_private_files(nomi_documenti)
        return jsonify({"errore": "Email già in uso"}), 409
    except Exception:
        conn.rollback()
        delete_private_files(nomi_documenti)
        return jsonify({"errore": "Registrazione non completata"}), 400
    finally:
        cursor.close()
        conn.close()

# --- 2. LOGIN ---
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
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

    password_valida = False
    if utente:
        try:
            password_valida = check_password_hash(utente['password'], pwd)
        except ValueError:
            password_valida = False
    if utente and utente['stato_account'] == 'ATTIVO' and password_valida:
        token = jwt.encode({'id_utente': utente['id_utente'], 'ruolo': utente['ruolo'],
                            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)},
                           app.config['SECRET_KEY'], algorithm="HS256")
        conn = get_db_connection()
        if conn:
            try:
                registra_attivita(conn, utente['id_utente'], 'ACCESSO')
                conn.commit()
            finally:
                conn.close()
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
    if file.mimetype not in {'image/jpeg', 'image/png', 'image/webp', 'video/mp4', 'video/webm', 'video/quicktime'}:
        return jsonify({"errore": "L'allegato deve essere una foto o un video valido"}), 400
    nome_file = secure_filename(file.filename)
    if not nome_file:
        return jsonify({"errore": "Nome allegato non valido"}), 400
    if storage_client is None:
        return jsonify({"errore": "Storage allegati non configurato"}), 503
    nome_file = f"{uuid.uuid4().hex}_{nome_file}"
    try:
        percorso, dimensione_bytes = upload_private_file(file, 'allegati', nome_file)
    except Exception:
        return jsonify({"errore": "Salvataggio dell'allegato non riuscito"}), 503

    conn = get_db_connection()
    if conn is None:
        delete_private_files([percorso])
        return jsonify({"errore": "Database non disponibile"}), 503

    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO segnalazione (titolo, descrizione, id_autore, id_quartiere, id_stato_corrente) VALUES (%s, %s, %s, %s, 1)",
                       (titolo, descrizione, current_user['id_utente'], id_quartiere))
        id_seg = cursor.lastrowid
        cursor.execute("INSERT INTO allegato (nome_file, percorso_file, tipo_mime, tipo_media, dimensione_bytes, id_segnalazione) VALUES (%s, %s, %s, %s, %s, %s)",
                       (nome_file, percorso, file.mimetype, 'IMMAGINE' if 'image' in file.mimetype else 'VIDEO', dimensione_bytes, id_seg))
        registra_attivita(conn, current_user['id_utente'], 'CREAZIONE_SEGNALAZIONE', 'SEGNALAZIONE', id_seg)
        conn.commit()
        return jsonify({"id_segnalazione": id_seg}), 201
    except Exception as e:
        conn.rollback()
        delete_private_files([percorso])
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
        registra_attivita(conn, current_user['id_utente'], 'VOTO', 'SEGNALAZIONE', id_segnalazione)
        conn.commit()
        return jsonify({"messaggio": "Sostegno aggiunto!"}), 201
    except mysql.connector.Error:
        return jsonify({"errore": "Impossibile sostenere questa segnalazione (forse è la tua o hai già votato)."}), 400
    finally:
        cursor.close()
        conn.close()

@app.route('/api/profilo', methods=['GET', 'PUT', 'DELETE'])
@token_required
def profilo(current_user):
    id_utente = current_user['id_utente']
    conn = get_db_connection()
    if conn is None:
        return jsonify({"errore": "Database non disponibile"}), 503
    cursor = conn.cursor(dictionary=True)
    try:
        if request.method == 'GET':
            cursor.execute("""SELECT id_utente, nome, cognome, email, codice_fiscale,
                indirizzo_residenza, data_nascita, ruolo, stato_account
                FROM utente WHERE id_utente = %s""", (id_utente,))
            risultato = cursor.fetchone()
            return jsonify(risultato or {}), 200
        if request.method == 'DELETE':
            registra_attivita(conn, id_utente, 'ELIMINAZIONE_ACCOUNT')
            cursor.execute("DELETE FROM utente WHERE id_utente = %s", (id_utente,))
            conn.commit()
            return jsonify({"messaggio": "Account eliminato"}), 200

        dati = request.get_json(silent=True) or {}
        consentiti = {'nome', 'cognome', 'indirizzo_residenza'}
        aggiornamenti = {chiave: str(valore).strip() for chiave, valore in dati.items()
                         if chiave in consentiti and str(valore).strip()}
        if not aggiornamenti:
            return jsonify({"errore": "Nessun dato modificabile"}), 400
        clausola = ', '.join(f'{chiave} = %s' for chiave in aggiornamenti)
        cursor.execute(f"UPDATE utente SET {clausola} WHERE id_utente = %s",
                       (*aggiornamenti.values(), id_utente))
        registra_attivita(conn, id_utente, 'MODIFICA_PROFILO', dettagli=','.join(aggiornamenti))
        conn.commit()
        return jsonify({"messaggio": "Profilo aggiornato"}), 200
    finally:
        cursor.close()
        conn.close()

@app.route('/api/segnalazioni/mie', methods=['GET'])
@token_required
def mie_segnalazioni(current_user):
    conn = get_db_connection()
    if conn is None:
        return jsonify({"errore": "Database non disponibile"}), 503
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""SELECT s.*, q.nome AS quartiere, st.nome AS stato
            FROM segnalazione s
            LEFT JOIN quartiere q ON q.id_quartiere = s.id_quartiere
            LEFT JOIN stato_segnalazione st ON st.id_stato = s.id_stato_corrente
            WHERE s.id_autore = %s ORDER BY s.id_segnalazione DESC""", (current_user['id_utente'],))
        return jsonify(cursor.fetchall()), 200
    finally:
        cursor.close()
        conn.close()

@app.route('/api/segnalazioni/<int:id_segnalazione>', methods=['PUT', 'DELETE'])
@token_required
def gestisci_segnalazione(current_user, id_segnalazione):
    conn = get_db_connection()
    if conn is None:
        return jsonify({"errore": "Database non disponibile"}), 503
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id_autore FROM segnalazione WHERE id_segnalazione = %s", (id_segnalazione,))
        segnalazione = cursor.fetchone()
        autorizzato = segnalazione and (segnalazione['id_autore'] == current_user['id_utente'] or current_user.get('ruolo') == 'COMITATO')
        if not autorizzato:
            return jsonify({"errore": "Non autorizzato"}), 403
        if request.method == 'DELETE':
            cursor.execute("DELETE FROM segnalazione WHERE id_segnalazione = %s", (id_segnalazione,))
            registra_attivita(conn, current_user['id_utente'], 'ELIMINAZIONE_SEGNALAZIONE', 'SEGNALAZIONE', id_segnalazione)
            conn.commit()
            return jsonify({"messaggio": "Segnalazione eliminata"}), 200
        dati = request.get_json(silent=True) or {}
        if not dati.get('titolo') or not dati.get('descrizione'):
            return jsonify({"errore": "Titolo e descrizione sono obbligatori"}), 400
        cursor.execute("UPDATE segnalazione SET titolo = %s, descrizione = %s WHERE id_segnalazione = %s",
                       (dati['titolo'].strip(), dati['descrizione'].strip(), id_segnalazione))
        registra_attivita(conn, current_user['id_utente'], 'MODIFICA_SEGNALAZIONE', 'SEGNALAZIONE', id_segnalazione)
        conn.commit()
        return jsonify({"messaggio": "Segnalazione aggiornata"}), 200
    finally:
        cursor.close()
        conn.close()

@app.route('/api/segnalazioni/<int:id_segnalazione>/commenti', methods=['GET', 'POST'])
@token_required
def commenti(current_user, id_segnalazione):
    conn = get_db_connection()
    if conn is None:
        return jsonify({"errore": "Database non disponibile"}), 503
    cursor = conn.cursor(dictionary=True)
    try:
        if request.method == 'GET':
            cursor.execute("""SELECT c.id_commento, c.testo, c.data_creazione,
                c.id_utente, CONCAT(u.nome, ' ', LEFT(u.cognome, 1), '.') AS autore
                FROM commento c JOIN utente u ON u.id_utente = c.id_utente
                WHERE c.id_segnalazione = %s ORDER BY c.data_creazione ASC""", (id_segnalazione,))
            return jsonify(cursor.fetchall()), 200
        testo = (request.get_json(silent=True) or {}).get('testo', '').strip()
        if not testo:
            return jsonify({"errore": "Il commento non può essere vuoto"}), 400
        cursor.execute("INSERT INTO commento (testo, id_utente, id_segnalazione) VALUES (%s, %s, %s)",
                       (testo, current_user['id_utente'], id_segnalazione))
        registra_attivita(conn, current_user['id_utente'], 'INSERIMENTO_COMMENTO', 'SEGNALAZIONE', id_segnalazione)
        conn.commit()
        return jsonify({"messaggio": "Commento pubblicato"}), 201
    finally:
        cursor.close()
        conn.close()

@app.route('/api/commenti/<int:id_commento>', methods=['PUT', 'DELETE'])
@token_required
def gestisci_commento(current_user, id_commento):
    conn = get_db_connection()
    if conn is None:
        return jsonify({"errore": "Database non disponibile"}), 503
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id_utente FROM commento WHERE id_commento = %s", (id_commento,))
        commento = cursor.fetchone()
        if not commento or (commento['id_utente'] != current_user['id_utente'] and current_user.get('ruolo') != 'COMITATO'):
            return jsonify({"errore": "Non autorizzato"}), 403
        if request.method == 'DELETE':
            cursor.execute("DELETE FROM commento WHERE id_commento = %s", (id_commento,))
            registra_attivita(conn, current_user['id_utente'], 'ELIMINAZIONE_COMMENTO', 'COMMENTO', id_commento)
        else:
            testo = (request.get_json(silent=True) or {}).get('testo', '').strip()
            if not testo:
                return jsonify({"errore": "Il commento non può essere vuoto"}), 400
            cursor.execute("UPDATE commento SET testo = %s WHERE id_commento = %s", (testo, id_commento))
            registra_attivita(conn, current_user['id_utente'], 'MODIFICA_COMMENTO', 'COMMENTO', id_commento)
        conn.commit()
        return jsonify({"messaggio": "Commento aggiornato"}), 200
    finally:
        cursor.close()
        conn.close()

@app.route('/api/miei-voti', methods=['GET'])
@token_required
def miei_voti(current_user):
    conn = get_db_connection()
    if conn is None:
        return jsonify({"errore": "Database non disponibile"}), 503
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""SELECT s.*, q.nome AS quartiere, st.nome AS stato
            FROM sostegno so JOIN segnalazione s ON s.id_segnalazione = so.id_segnalazione
            LEFT JOIN quartiere q ON q.id_quartiere = s.id_quartiere
            LEFT JOIN stato_segnalazione st ON st.id_stato = s.id_stato_corrente
            WHERE so.id_utente = %s ORDER BY so.id_sostegno DESC""", (current_user['id_utente'],))
        return jsonify(cursor.fetchall()), 200
    finally:
        cursor.close()
        conn.close()

@app.route('/api/comitato/segnalazioni', methods=['GET'])
@token_required
def segnalazioni_comitato(current_user):
    if current_user.get('ruolo') != 'COMITATO':
        return jsonify({"errore": "Accesso riservato al comitato"}), 403
    conn = get_db_connection()
    if conn is None:
        return jsonify({"errore": "Database non disponibile"}), 503
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""SELECT s.*, u.nome, u.cognome, u.email, q.nome AS quartiere,
            st.nome AS stato FROM segnalazione s JOIN utente u ON u.id_utente = s.id_autore
            LEFT JOIN quartiere q ON q.id_quartiere = s.id_quartiere
            LEFT JOIN stato_segnalazione st ON st.id_stato = s.id_stato_corrente
            ORDER BY s.id_segnalazione DESC""")
        return jsonify(cursor.fetchall()), 200
    finally:
        cursor.close()
        conn.close()

@app.route('/api/comitato/utenti-in-verifica', methods=['GET'])
@token_required
def utenti_in_verifica(current_user):
    if current_user.get('ruolo') != 'COMITATO':
        return jsonify({"errore": "Accesso riservato al comitato"}), 403
    conn = get_db_connection()
    if conn is None:
        return jsonify({"errore": "Database non disponibile"}), 503
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""SELECT id_utente, nome, cognome, email, codice_fiscale,
            indirizzo_residenza, data_nascita, documento_fronte, documento_retro
            FROM utente WHERE stato_account = 'IN_VERIFICA'
            ORDER BY data_creazione ASC""")
        return jsonify(cursor.fetchall()), 200
    finally:
        cursor.close()
        conn.close()

@app.route('/api/comitato/utenti/<int:id_utente>/verifica', methods=['POST'])
@token_required
def verifica_utente(current_user, id_utente):
    if current_user.get('ruolo') != 'COMITATO':
        return jsonify({"errore": "Accesso riservato al comitato"}), 403
    stato = (request.get_json(silent=True) or {}).get('stato')
    if stato not in {'ATTIVO', 'RIFIUTATO'}:
        return jsonify({"errore": "Stato di verifica non valido"}), 400
    conn = get_db_connection()
    if conn is None:
        return jsonify({"errore": "Database non disponibile"}), 503
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE utente SET stato_account = %s WHERE id_utente = %s", (stato, id_utente))
        registra_attivita(conn, current_user['id_utente'], 'VERIFICA_ACCOUNT', 'UTENTE', id_utente, stato)
        conn.commit()
        return jsonify({"messaggio": f"Account {stato.lower()}"}), 200
    finally:
        cursor.close()
        conn.close()

@app.route('/api/comitato/segnalazioni/<int:id_segnalazione>/analisi', methods=['POST'])
@token_required
def analizza_segnalazione(current_user, id_segnalazione):
    if current_user.get('ruolo') != 'COMITATO':
        return jsonify({"errore": "Accesso riservato al comitato"}), 403
    conn = get_db_connection()
    if conn is None:
        return jsonify({"errore": "Database non disponibile"}), 503
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT titolo, descrizione FROM segnalazione WHERE id_segnalazione = %s", (id_segnalazione,))
        proposta = cursor.fetchone()
        if not proposta:
            return jsonify({"errore": "Segnalazione non trovata"}), 404
        testo = f"{proposta['titolo']} {proposta['descrizione']}".lower()
        parole_urgenza = {'pericolo', 'sicurezza', 'incidente', 'allagamento', 'urgente'}
        parole_ambiente = {'verde', 'rifiuti', 'alberi', 'inquinamento', 'parco'}
        parole_trasporti = {'bus', 'metro', 'tram', 'traffico', 'strada', 'marciapiede'}
        categorie = {'sicurezza': parole_urgenza, 'ambiente': parole_ambiente, 'mobilità': parole_trasporti}
        categoria = max(categorie, key=lambda nome: sum(parola in testo for parola in categorie[nome]))
        urgenza = min(100, 35 + sum(parola in testo for parola in parole_urgenza) * 13 + min(len(testo) // 160, 25))
        registra_attivita(conn, current_user['id_utente'], 'ANALISI_IA', 'SEGNALAZIONE', id_segnalazione, categoria)
        conn.commit()
        return jsonify({"categoria": categoria, "indice_urgenza": urgenza,
                        "nota": "Analisi automatica di supporto: la decisione finale spetta al comitato."}), 200
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(debug=True, port=5000)