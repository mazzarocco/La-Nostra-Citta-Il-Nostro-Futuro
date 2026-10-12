# La Nostra Citta, Il Nostro Futuro

Applicazione civica per segnalazioni, proposte e partecipazione dei cittadini di Milano.

## Avvio backend

1. Crea un ambiente virtuale e installa le dipendenze:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Configura `.env` con `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` e `JWT_SECRET_KEY`. Non sono richieste variabili `STORAGE_*`: il progetto non usa S3, R2 o altri bucket.
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
```

Le registrazioni e le segnalazioni non richiedono allegati. I documenti d'identita non vengono richiesti, salvati o verificati in questa versione dimostrativa.

## Avvio frontend

```bash
cd la-nostra-citta-frontend
npm install
npm start
```

Apri `http://localhost:4200`.

## Account dimostrativi

Le nuove registrazioni vengono create direttamente come `ATTIVO`, quindi si puo effettuare il login subito dopo la registrazione. Questa versione non verifica l'identita degli utenti: non usare il flusso dimostrativo in produzione senza aggiungere un'autenticazione adeguata.

## Migrazione database esistente

Se il database Aiven e gia stato creato con i documenti obbligatori, applica una sola volta [sql/20261012_rimuovi_obbligo_documenti.sql](sql/20261012_rimuovi_obbligo_documenti.sql). La migrazione modifica solo la nullabilita delle due colonne e lo stato predefinito; non elimina tabelle o dati.

La tabella `allegato` puo restare nel database per compatibilita con dati storici, ma la creazione delle nuove segnalazioni non la usa. La vista `v_segnalazioni_pubbliche` e le tabelle `quartiere`, `stato_segnalazione`, `sostegno`, `commento` e `log_attivita` sono definite in `schema.sql` e usate da `app.py`.
