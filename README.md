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

## Deploy backend Flask su Vercel

Il backend usa il supporto Flask ufficiale di Vercel con `app.py` nella root del progetto. Nel progetto Vercel seleziona la root del repository e configura le variabili seguenti:

```text
APP_ENV=production
JWT_SECRET_KEY=<chiave casuale lunga almeno 32 caratteri>
DB_HOST=<host MySQL Aiven>
DB_PORT=<porta MySQL Aiven>
DB_USER=<utente MySQL Aiven>
DB_PASSWORD=<password MySQL Aiven>
DB_NAME=<database MySQL Aiven>
DB_SSL_CA_CONTENT=<certificato CA Aiven completo>
STORAGE_BUCKET=<bucket privato S3-compatibile>
STORAGE_ENDPOINT_URL=<endpoint dello storage>
STORAGE_REGION=<regione dello storage>
STORAGE_ACCESS_KEY_ID=<chiave storage>
STORAGE_SECRET_ACCESS_KEY=<segreto storage>
```

I documenti d'identita, le immagini e i video vengono salvati nel bucket privato e nel database vengono memorizzate solo le chiavi degli oggetti. Non usare `uploads/` su Vercel per la persistenza: il filesystem delle funzioni e temporaneo. Il bucket deve restare privato e i documenti devono essere letti solo tramite un futuro endpoint autenticato con URL firmati.

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
