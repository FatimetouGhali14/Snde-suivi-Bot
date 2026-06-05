-- =====================================================================
-- SNDE Suivi POC - Instructions, rapports quotidiens et alertes
-- =====================================================================

CREATE TABLE instructions (
    id              SERIAL PRIMARY KEY,
    reference       VARCHAR(50) UNIQUE NOT NULL,
    direction_code  VARCHAR(10) NOT NULL,
    action          TEXT NOT NULL,
    delai           DATE,
    priorite        VARCHAR(20) NOT NULL DEFAULT 'normal',
    statut_reponse  VARCHAR(20) NOT NULL DEFAULT 'en_attente',
    date_envoi_dg   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    date_reponse    TIMESTAMPTZ
);

CREATE INDEX idx_instructions_direction ON instructions(direction_code);
CREATE INDEX idx_instructions_statut    ON instructions(statut_reponse);


CREATE TABLE rapports_quotidiens (
    id              SERIAL PRIMARY KEY,
    instruction_id  INT NOT NULL REFERENCES instructions(id) ON DELETE CASCADE,
    directeur_uuid  UUID NOT NULL REFERENCES directeurs(id),
    contenu         TEXT NOT NULL,
    date_rapport    DATE NOT NULL DEFAULT CURRENT_DATE,
    heure_envoi     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    statut          VARCHAR(20) NOT NULL,
    envoye_avant_21h BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT uq_rapport_instruction_directeur_date
        UNIQUE (instruction_id, directeur_uuid, date_rapport)
);

CREATE INDEX idx_rapports_quotidiens_date ON rapports_quotidiens(date_rapport DESC);


CREATE TABLE alertes (
    id               SERIAL PRIMARY KEY,
    instruction_id   INT NOT NULL REFERENCES instructions(id) ON DELETE CASCADE,
    type_alerte      VARCHAR(50) NOT NULL,
    envoye_dg        BOOLEAN NOT NULL DEFAULT FALSE,
    envoye_directeur BOOLEAN NOT NULL DEFAULT FALSE,
    date_envoi       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_alertes_instruction ON alertes(instruction_id);
