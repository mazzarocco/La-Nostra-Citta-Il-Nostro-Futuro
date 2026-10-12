-- Schema MySQL per La Nostra Citta.
-- Il file e idempotente: non elimina dati e non contiene DROP o TRUNCATE.

CREATE TABLE IF NOT EXISTS utente (
    id_utente BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    nome VARCHAR(100) NOT NULL,
    cognome VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL,
    codice_fiscale CHAR(16) NOT NULL,
    indirizzo_residenza VARCHAR(255) NOT NULL,
    data_nascita DATE NOT NULL,
    password VARCHAR(255) NOT NULL,
    documento_fronte VARCHAR(512) NULL,
    documento_retro VARCHAR(512) NULL,
    ruolo ENUM('CITTADINO', 'COMITATO') NOT NULL DEFAULT 'CITTADINO',
    stato_account ENUM('IN_VERIFICA', 'ATTIVO', 'RIFIUTATO') NOT NULL DEFAULT 'ATTIVO',
    data_creazione TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    data_aggiornamento TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id_utente),
    UNIQUE KEY uq_utente_email (email),
    UNIQUE KEY uq_utente_codice_fiscale (codice_fiscale),
    KEY idx_utente_stato_creazione (stato_account, data_creazione)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS quartiere (
    id_quartiere INT UNSIGNED NOT NULL AUTO_INCREMENT,
    nome VARCHAR(100) NOT NULL,
    PRIMARY KEY (id_quartiere),
    UNIQUE KEY uq_quartiere_nome (nome)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS stato_segnalazione (
    id_stato TINYINT UNSIGNED NOT NULL AUTO_INCREMENT,
    nome VARCHAR(50) NOT NULL,
    PRIMARY KEY (id_stato),
    UNIQUE KEY uq_stato_segnalazione_nome (nome)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS segnalazione (
    id_segnalazione BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    titolo VARCHAR(255) NOT NULL,
    descrizione TEXT NOT NULL,
    id_autore BIGINT UNSIGNED NOT NULL,
    id_quartiere INT UNSIGNED NOT NULL,
    id_stato_corrente TINYINT UNSIGNED NOT NULL DEFAULT 1,
    data_creazione TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    data_aggiornamento TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id_segnalazione),
    KEY idx_segnalazione_autore (id_autore),
    KEY idx_segnalazione_quartiere_stato (id_quartiere, id_stato_corrente),
    CONSTRAINT fk_segnalazione_autore
        FOREIGN KEY (id_autore) REFERENCES utente (id_utente)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_segnalazione_quartiere
        FOREIGN KEY (id_quartiere) REFERENCES quartiere (id_quartiere)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_segnalazione_stato
        FOREIGN KEY (id_stato_corrente) REFERENCES stato_segnalazione (id_stato)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS allegato (
    id_allegato BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    nome_file VARCHAR(255) NOT NULL,
    percorso_file VARCHAR(1024) NOT NULL,
    tipo_mime VARCHAR(100) NOT NULL,
    tipo_media ENUM('IMMAGINE', 'VIDEO') NOT NULL,
    dimensione_bytes BIGINT UNSIGNED NOT NULL,
    id_segnalazione BIGINT UNSIGNED NOT NULL,
    data_creazione TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id_allegato),
    KEY idx_allegato_segnalazione (id_segnalazione),
    CONSTRAINT fk_allegato_segnalazione
        FOREIGN KEY (id_segnalazione) REFERENCES segnalazione (id_segnalazione)
        ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS sostegno (
    id_sostegno BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    id_utente BIGINT UNSIGNED NOT NULL,
    id_segnalazione BIGINT UNSIGNED NOT NULL,
    data_creazione TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id_sostegno),
    UNIQUE KEY uq_sostegno_utente_segnalazione (id_utente, id_segnalazione),
    KEY idx_sostegno_segnalazione (id_segnalazione),
    CONSTRAINT fk_sostegno_utente
        FOREIGN KEY (id_utente) REFERENCES utente (id_utente)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_sostegno_segnalazione
        FOREIGN KEY (id_segnalazione) REFERENCES segnalazione (id_segnalazione)
        ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS commento (
    id_commento BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    testo TEXT NOT NULL,
    id_utente BIGINT UNSIGNED NOT NULL,
    id_segnalazione BIGINT UNSIGNED NOT NULL,
    data_creazione TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    data_aggiornamento TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id_commento),
    KEY idx_commento_segnalazione_data (id_segnalazione, data_creazione),
    KEY idx_commento_utente (id_utente),
    CONSTRAINT fk_commento_utente
        FOREIGN KEY (id_utente) REFERENCES utente (id_utente)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_commento_segnalazione
        FOREIGN KEY (id_segnalazione) REFERENCES segnalazione (id_segnalazione)
        ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS log_attivita (
    id_log BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    id_utente BIGINT UNSIGNED NULL,
    azione VARCHAR(80) NOT NULL,
    entita VARCHAR(80) NULL,
    id_entita BIGINT UNSIGNED NULL,
    dettagli TEXT NULL,
    data_creazione TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id_log),
    KEY idx_log_utente_data (id_utente, data_creazione),
    KEY idx_log_entita (entita, id_entita),
    CONSTRAINT fk_log_utente
        FOREIGN KEY (id_utente) REFERENCES utente (id_utente)
        ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT IGNORE INTO quartiere (id_quartiere, nome) VALUES
    (1, 'Centro Storico'),
    (2, 'Navigli'),
    (3, 'Isola'),
    (4, 'Bicocca'),
    (5, 'Lambrate'),
    (6, 'San Siro');

INSERT IGNORE INTO stato_segnalazione (id_stato, nome) VALUES
    (1, 'PUBBLICATA'),
    (2, 'IN_LAVORAZIONE'),
    (3, 'RISOLTA'),
    (4, 'ARCHIVIATA');

CREATE OR REPLACE VIEW v_segnalazioni_pubbliche AS
SELECT
    s.id_segnalazione,
    s.titolo,
    s.descrizione,
    s.id_autore,
    s.id_quartiere,
    s.id_stato_corrente,
    s.data_creazione,
    s.data_aggiornamento,
    q.nome AS quartiere,
    st.nome AS stato,
    COUNT(DISTINCT so.id_sostegno) AS numero_sostegni
FROM segnalazione AS s
JOIN quartiere AS q ON q.id_quartiere = s.id_quartiere
JOIN stato_segnalazione AS st ON st.id_stato = s.id_stato_corrente
LEFT JOIN sostegno AS so ON so.id_segnalazione = s.id_segnalazione
GROUP BY
    s.id_segnalazione,
    s.titolo,
    s.descrizione,
    s.id_autore,
    s.id_quartiere,
    s.id_stato_corrente,
    s.data_creazione,
    s.data_aggiornamento,
    q.nome,
    st.nome;