-- =====================================================================
-- SNDE Suivi POC - Schéma initial
-- 3 tables minimales pour valider le flux bout-en-bout sur 1 direction
-- =====================================================================

-- Extensions nécessaires
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";


-- =====================================================================
-- Table : directeurs
-- Référentiel des directeurs SNDE (pour le POC : 1 seul directeur PROD)
-- =====================================================================
CREATE TABLE directeurs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    matricule       VARCHAR(20) UNIQUE NOT NULL,
    nom_complet     VARCHAR(200) NOT NULL,
    direction_code  VARCHAR(10) NOT NULL,
    telegram_chat_id BIGINT UNIQUE,
    actif           BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_directeurs_chat_id 
    ON directeurs(telegram_chat_id) 
    WHERE telegram_chat_id IS NOT NULL;

COMMENT ON TABLE directeurs IS 'Référentiel RH des 12 directeurs SNDE';
COMMENT ON COLUMN directeurs.direction_code IS 'PROD, DIST, MAINT, ETN, STOCK, ACHAT, COM, INFO, QUAL, FIN, URG, AUDIT';


-- =====================================================================
-- Table : rapports
-- 1 rapport par directeur par jour (contrainte d'unicité forte)
-- =====================================================================
CREATE TABLE rapports (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    directeur_id    UUID NOT NULL REFERENCES directeurs(id),
    direction_code  VARCHAR(10) NOT NULL,
    date_rapport    DATE NOT NULL,
    statut_global   VARCHAR(20) NOT NULL,  -- vert, orange, rouge
    
    -- Métadonnées de réception
    fichier_nom         VARCHAR(255),
    fichier_taille_octets INT,
    recu_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Contenus textuels libres
    points_bloquants    TEXT[],     -- tableau Postgres, 0 à 3 éléments
    actions_demain      TEXT[],
    
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Anti-doublon : 1 rapport par directeur par jour maximum
    CONSTRAINT uq_rapports_directeur_date UNIQUE (directeur_id, date_rapport)
);

CREATE INDEX idx_rapports_date ON rapports(date_rapport DESC);
CREATE INDEX idx_rapports_direction_date ON rapports(direction_code, date_rapport DESC);

COMMENT ON CONSTRAINT uq_rapports_directeur_date ON rapports 
    IS 'Empêche un même directeur d''envoyer 2 rapports le même jour';


-- =====================================================================
-- Table : rapport_kpis
-- 8 lignes par rapport (les 8 KPIs de la direction)
-- =====================================================================
CREATE TABLE rapport_kpis (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rapport_id      UUID NOT NULL REFERENCES rapports(id) ON DELETE CASCADE,
    
    numero          INT NOT NULL,           -- 1 à 8
    libelle         VARCHAR(200) NOT NULL,
    unite           VARCHAR(20),
    
    valeur_j_moins_1    NUMERIC,            -- nullable
    valeur_jour         NUMERIC,            -- nullable si KPI texte (statut)
    valeur_jour_texte   VARCHAR(100),       -- pour les KPIs type "oui/non"
    objectif            NUMERIC,
    
    observations    TEXT,
    statut          VARCHAR(20) NOT NULL,   -- vert, orange, rouge, non_renseigne
    
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT uq_rapport_kpi_numero UNIQUE (rapport_id, numero)
);

CREATE INDEX idx_kpis_rapport ON rapport_kpis(rapport_id);


-- =====================================================================
-- Données initiales : 1 directeur de test pour le POC
-- À remplacer par le vrai chat_id quand le bot sera créé
-- =====================================================================
INSERT INTO directeurs (matricule, nom_complet, direction_code, telegram_chat_id)
VALUES ('TEST001', 'Directeur Test PROD', 'PROD', NULL);