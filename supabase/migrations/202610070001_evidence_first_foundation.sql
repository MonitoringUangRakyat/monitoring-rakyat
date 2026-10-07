-- Prepared migration. Not applied until a Supabase project is connected.
create schema if not exists raw;
create schema if not exists core;
create schema if not exists evidence;
create schema if not exists forensic;
create schema if not exists audit;
create schema if not exists ops;

create table if not exists evidence.sources(
 id uuid primary key default gen_random_uuid(),
 source_key text not null unique,
 name text not null,
 source_class text not null,
 authority_score smallint check(authority_score between 0 and 100),
 canonical_url text,
 active boolean not null default true,
 created_at timestamptz not null default now()
);
alter table evidence.sources enable row level security;

create table if not exists raw.source_payloads(
 id uuid primary key default gen_random_uuid(),
 source_id uuid references evidence.sources(id),
 captured_at timestamptz not null default now(),
 source_url text,
 content_hash text not null,
 payload jsonb not null,
 unique(source_id,content_hash)
);
alter table raw.source_payloads enable row level security;

create table if not exists evidence.documents(
 id uuid primary key default gen_random_uuid(),
 source_id uuid not null references evidence.sources(id),
 source_payload_id uuid references raw.source_payloads(id),
 canonical_url text,
 sha256 text not null,
 captured_at timestamptz not null default now(),
 metadata jsonb not null default '{}'::jsonb,
 unique(source_id,sha256)
);
alter table evidence.documents enable row level security;

create table if not exists core.findings(
 id uuid primary key default gen_random_uuid(),
 finding_type text not null,
 title text not null,
 period_start date,
 period_end date,
 amount_idr numeric,
 verification_status text not null default 'DRAFT_UNVERIFIED',
 confidence numeric check(confidence between 0 and 100),
 created_at timestamptz not null default now(),
 updated_at timestamptz not null default now()
);
alter table core.findings enable row level security;

create table if not exists evidence.finding_evidence(
 finding_id uuid not null references core.findings(id) on delete restrict,
 document_id uuid not null references evidence.documents(id) on delete restrict,
 relation text not null default 'SUPPORTS',
 citation text,
 created_at timestamptz not null default now(),
 primary key(finding_id,document_id)
);
alter table evidence.finding_evidence enable row level security;

create table if not exists ops.source_health(
 source_id uuid primary key references evidence.sources(id),
 status text not null,
 last_attempt timestamptz,
 last_success timestamptz,
 consecutive_failures integer not null default 0,
 latency_ms integer,
 checksum text,
 failure_reason text,
 next_retry timestamptz,
 updated_at timestamptz not null default now()
);
alter table ops.source_health enable row level security;

create table if not exists ops.dead_letter_queue(
 id uuid primary key default gen_random_uuid(),
 source_id uuid references evidence.sources(id),
 payload_id uuid references raw.source_payloads(id),
 failure_stage text not null,
 failure_reason text not null,
 attempts integer not null default 0,
 next_retry timestamptz,
 status text not null default 'OPEN',
 created_at timestamptz not null default now()
);
alter table ops.dead_letter_queue enable row level security;

-- No public policies are created here. Service-side ingestion uses privileged credentials.
-- Public read access must be exposed later through deliberate security-invoker views/RPC.
