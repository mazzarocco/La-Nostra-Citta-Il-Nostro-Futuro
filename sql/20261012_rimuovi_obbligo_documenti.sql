-- Migrazione non distruttiva per registrazioni senza documenti.
-- Eseguire una sola volta sul database Aiven dopo aver fatto un backup.

ALTER TABLE utente
    MODIFY documento_fronte VARCHAR(512) NULL,
    MODIFY documento_retro VARCHAR(512) NULL,
    MODIFY stato_account ENUM('IN_VERIFICA', 'ATTIVO', 'RIFIUTATO') NOT NULL DEFAULT 'ATTIVO';

-- Le registrazioni gia presenti in attesa non hanno piu una verifica identita da attendere.
UPDATE utente
SET stato_account = 'ATTIVO'
WHERE stato_account = 'IN_VERIFICA';
