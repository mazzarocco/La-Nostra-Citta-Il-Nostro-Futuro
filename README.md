# La Nostra Citta, Il Nostro Futuro

Applicazione civica per segnalazioni, proposte e partecipazione dei cittadini di Milano.

## Avvio backend

1. Crea un ambiente virtuale e installa le dipendenze:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Configura `.env` con `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` e `JWT_SECRET_KEY`.
3. Inizializza il database eseguendo `schema.sql` su MySQL:

```bash
mysql -h "$DB_HOST" -P "${DB_PORT:-3306}" -u "$DB_USER" -p "$DB_NAME" < schema.sql
```

4. Avvia l'API:

```bash
python app.py
```

L'API e disponibile su `http://localhost:5000`.

## Avvio frontend

```bash
cd la-nostra-citta-frontend
npm install
npm start
```

Apri `http://localhost:4200`.

## Verifica account

Le nuove registrazioni vengono salvate come `IN_VERIFICA`. Un membro autorizzato deve portare l'account a `ATTIVO` prima del login, ad esempio tramite SQL:

```sql
UPDATE utente SET stato_account = 'ATTIVO' WHERE email = 'cittadino@example.com';
```

Le immagini dei documenti restano nella cartella `uploads/` e non sono esposte dalle API pubbliche.
