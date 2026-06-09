ALTER TABLE rapports_quotidiens
    ADD COLUMN IF NOT EXISTS telegram_file_id VARCHAR(255);

ALTER TABLE rapports_quotidiens
    ADD COLUMN IF NOT EXISTS nom_fichier VARCHAR(255);

COMMENT ON COLUMN rapports_quotidiens.telegram_file_id IS 
    'ID Telegram du fichier Excel (pour retransmission/fusion)';