-- =====================================================================
-- SNDE Suivi POC - instruction_id devient optionnel
-- =====================================================================
-- Permet d'enregistrer un rapport quotidien SANS qu'une instruction
-- du DG soit préalablement créée.
-- 
-- Workflow visé : le directeur envoie son rapport de sa propre 
-- initiative, sans attendre d'instruction. Le champ instruction_id
-- ne sert que dans le cas où le rapport répond à une instruction
-- précise du DG.
-- =====================================================================

ALTER TABLE rapports_quotidiens 
    ALTER COLUMN instruction_id DROP NOT NULL;

COMMENT ON COLUMN rapports_quotidiens.instruction_id IS 
    'Optionnel : lié à une instruction si le rapport y répond, NULL sinon';