-- =====================================================================
-- SNDE Suivi POC - Table de suivi du message de synthèse DG
-- =====================================================================
-- Stocke l'ID du message Telegram pinné côté DG pour pouvoir l'éditer
-- à chaque nouveau rapport reçu.
-- 1 ligne par jour : on garde l'historique des synthèses.
-- =====================================================================

CREATE TABLE IF NOT EXISTS synthese_dg (
    id              SERIAL PRIMARY KEY,
    date_synthese   DATE NOT NULL UNIQUE,
    chat_id_dg      BIGINT NOT NULL,
    message_id      BIGINT,
    derniere_maj    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_synthese_dg_date 
    ON synthese_dg(date_synthese DESC);

COMMENT ON TABLE synthese_dg IS 
    'Suivi du message Telegram de synthèse envoyé au DG chaque jour';
COMMENT ON COLUMN synthese_dg.message_id IS 
    'ID du message Telegram à éditer pour mettre à jour la synthèse';
    