-- Applied by the agent on every start, so every statement must be idempotent.
CREATE TABLE IF NOT EXISTS triages (
    id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    alert       text        NOT NULL,
    fingerprint text        NOT NULL,
    severity    text        NOT NULL,
    created_at  timestamptz NOT NULL,
    body        jsonb       NOT NULL
);

CREATE INDEX IF NOT EXISTS triages_alert_created_at ON triages (alert, created_at DESC);
