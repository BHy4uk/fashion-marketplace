"""Analytics bounded context (DOMAIN-012) — read-only reporting read models.

Analytics is inherently cross-cutting: it derives aggregate metrics from the
persisted state of other modules. It NEVER writes to any collection and never
participates in business decisions — it is a pure query/reporting surface."""
