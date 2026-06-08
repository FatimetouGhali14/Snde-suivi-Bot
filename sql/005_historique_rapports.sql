-- =====================================================================
-- SNDE Suivi POC - Historique des versions de rapports
-- =====================================================================
-- Ajoute une colonne 'version' à rapports_quotidiens pour permettre
-- les renvois correctifs sans perte d'historique.
-- 
-- Logique : un directeur peut envoyer plusieurs versions le même jour.
-- La dernière version (version la plus élevée) est la version "active".
-- =====================================================================

ALTER TABLE rapports_quotidiens 
    ADD COLUMN IF NOT EXISTS version INTEGER NOT NULL DEFAULT 1;

ALTER TABLE rapports_quotidiens 
    ADD COLUMN IF NOT EXISTS est_actif BOOLEAN NOT NULL DEFAULT TRUE;

-- Index pour retrouver rapidement la version active du jour
CREATE INDEX IF NOT EXISTS idx_rapports_actif 
    ON rapports_quotidiens(directeur_uuid, date_rapport, est_actif) 
    WHERE est_actif = TRUE;

COMMENT ON COLUMN rapports_quotidiens.version IS 
    'Numéro de version : 1, 2, 3... à chaque renvoi correctif';
COMMENT ON COLUMN rapports_quotidiens.est_actif IS 
    'TRUE pour la version la plus récente, FALSE pour les anciennes';


-- Suppression de la contrainte UNIQUE qui bloquerait les versions
-- (un directeur peut maintenant envoyer plusieurs versions le même jour)
ALTER TABLE rapports_quotidiens 
    DROP CONSTRAINT IF EXISTS uq_rapport_instruction_directeur_date;