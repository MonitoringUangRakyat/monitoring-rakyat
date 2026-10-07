# Autonomous 24/7 Operating Contract

The live system follows these invariants:

1. No source = no fact.
2. No evidence = no verified record.
3. No validation = no promotion.
4. Failure creates retry/recovery work; it must not silently disappear.
5. Every UNKNOWN becomes a task.
6. AI output is a claim; public data is verified evidence.

State flow:

`DISCOVERED -> DRAFT -> VERIFYING -> VERIFIED -> PUBLISHABLE`

Failure flow:

`FAILED -> RETRY -> RECOVERY -> DEAD_LETTER/ESCALATE`

The source layer is official-first. Media may discover leads, but cannot independently promote a claim to public fact.

Operational files:
- `dashboard/source_health.json`
- `dashboard/official_source_discovery.json`
- `dashboard/autonomous_tasks.json`
- `dashboard/autonomy_status.json`
- `dashboard/watchdog_status.json`
- `dashboard/promotion_gate.json`
- `dashboard/publication_gate_status.json`

A closed promotion gate blocks promotion and indicates that operators/agents must repair the failing dependency instead of inventing data.
