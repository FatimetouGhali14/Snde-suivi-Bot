-- =====================================================================
-- SNDE Suivi POC - Seed des 13 utilisateurs (12 directeurs + 1 DG)
-- =====================================================================
-- À exécuter après 001_init_poc.sql et 002_instructions_rapports.sql
-- 
-- Les telegram_chat_id sont volontairement NULL : chaque développeur
-- configure ses propres IDs de test localement (cf. README).
-- =====================================================================

INSERT INTO directeurs (matricule, nom_complet, direction_code, telegram_chat_id) VALUES
    ('PROD001',  'Directeur Production',             'PROD',  NULL),
    ('DIST001',  'Directeur Distribution',           'DIST',  NULL),
    ('MAINT001', 'Directeur Maintenance',            'MAINT', NULL),
    ('ETN001',   'Directeur Etudes & Travaux Neufs', 'ETN',   NULL),
    ('STOCK001', 'Directeur Stocks',                 'STOCK', NULL),
    ('ACHAT001', 'Directeur Achats',                 'ACHAT', NULL),
    ('COM001',   'Directeur Commercial',             'COM',   NULL),
    ('INFO001',  'Directeur Informatique',           'INFO',  NULL),
    ('QUAL001',  'Directeur Qualite de l eau',       'QUAL',  NULL),
    ('FIN001',   'Directeur Financier & Comptable',  'FIN',   NULL),
    ('URG001',   'Directeur Urgences',               'URG',   NULL),
    ('AUDIT001', 'Directeur Audit & Controle',       'AUDIT', NULL),
    ('DG001',    'Directeur General',                'DG',    NULL)
ON CONFLICT (matricule) DO NOTHING;

-- Note : après exécution, chaque développeur met à jour SES PROPRES IDs :
-- UPDATE directeurs SET telegram_chat_id = MON_CHAT_ID WHERE matricule = 'DG001';
-- UPDATE directeurs SET telegram_chat_id = MON_CHAT_ID WHERE matricule = 'PROD001';