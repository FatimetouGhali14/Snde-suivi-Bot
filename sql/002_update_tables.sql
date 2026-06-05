-- sql/002_update_tables.sql

-- Table instructions
CREATE TABLE IF NOT EXISTS instructions (
    id              SERIAL PRIMARY KEY,
    reference       VARCHAR(20) UNIQUE NOT NULL,
    direction_code  VARCHAR(10) NOT NULL,
    action          TEXT NOT NULL,
    delai           DATE,
    priorite        VARCHAR(10) DEFAULT 'normal',
    statut_reponse  VARCHAR(20) DEFAULT 'en_attente',
    date_envoi_dg   TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    date_reponse    TIMESTAMP WITH TIME ZONE,
    heure_limite    TIME DEFAULT '21:00'
);

-- Table rapports_quotidiens
-- directeur_uuid référence directeurs(id) qui est UUID
CREATE TABLE IF NOT EXISTS rapports_quotidiens (
    id               SERIAL PRIMARY KEY,
    instruction_id   INTEGER REFERENCES instructions(id),
    directeur_uuid   UUID REFERENCES directeurs(id),
    contenu          TEXT NOT NULL,
    date_rapport     DATE DEFAULT CURRENT_DATE,
    heure_envoi      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    statut           VARCHAR(20) DEFAULT 'a_l_heure',
    envoye_avant_21h BOOLEAN DEFAULT TRUE
);

-- Table alertes
CREATE TABLE IF NOT EXISTS alertes (
    id               SERIAL PRIMARY KEY,
    instruction_id   INTEGER REFERENCES instructions(id),
    type_alerte      VARCHAR(30) NOT NULL,
    date_envoi       TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    envoye_dg        BOOLEAN DEFAULT FALSE,
    envoye_directeur BOOLEAN DEFAULT FALSE
);

-- Index
CREATE INDEX IF NOT EXISTS idx_instructions_direction
    ON instructions(direction_code);
CREATE INDEX IF NOT EXISTS idx_instructions_statut
    ON instructions(statut_reponse);
CREATE INDEX IF NOT EXISTS idx_rapports_date
    ON rapports_quotidiens(date_rapport);
CREATE INDEX IF NOT EXISTS idx_alertes_instruction
    ON alertes(instruction_id);