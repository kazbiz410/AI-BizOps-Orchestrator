create extension if not exists "pgcrypto";

create or replace function set_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

create table if not exists organizations (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  industry text,
  employee_count integer,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists departments (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references organizations(id) on delete cascade,
  name text not null,
  lead_name text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists tools (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references organizations(id) on delete cascade,
  name text not null,
  category text not null,
  monthly_cost numeric(12, 2) not null default 0,
  ai_enabled boolean not null default false,
  vendor text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists tool_integrations (
  id uuid primary key default gen_random_uuid(),
  source_tool_id uuid not null references tools(id) on delete cascade,
  target_tool_id uuid not null references tools(id) on delete cascade,
  integration_type text not null,
  status text not null default 'planned',
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists business_processes (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references organizations(id) on delete cascade,
  department_id uuid references departments(id) on delete set null,
  name text not null,
  process_type text,
  raw_input_text text not null,
  kpi_summary text,
  challenge_summary text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists process_steps (
  id uuid primary key default gen_random_uuid(),
  process_id uuid not null references business_processes(id) on delete cascade,
  step_order integer not null,
  step_name text not null,
  actor text,
  input_data text,
  output_data text,
  tool_ids jsonb not null default '[]'::jsonb,
  manual_work boolean not null default false,
  approval_required boolean not null default false,
  ai_candidate boolean not null default false,
  automation_candidate boolean not null default false,
  human_approval_candidate boolean not null default false,
  issue_tags jsonb not null default '[]'::jsonb,
  meeting_related boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists ai_transform_patterns (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references organizations(id) on delete cascade,
  name text not null,
  source_format text,
  target_format text,
  description text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists findings (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references organizations(id) on delete cascade,
  process_id uuid references business_processes(id) on delete set null,
  title text not null,
  finding_type text not null,
  severity text not null,
  evidence jsonb not null default '{}'::jsonb,
  summary text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists recommendations (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references organizations(id) on delete cascade,
  finding_id uuid references findings(id) on delete set null,
  type text not null,
  title text not null,
  description text not null,
  priority_score integer not null default 0,
  roi_score integer not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists interview_questions (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references organizations(id) on delete cascade,
  process_id uuid references business_processes(id) on delete set null,
  assignee text,
  question text not null,
  reason text,
  slack_message text,
  status text not null default 'draft',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists interview_answers (
  id uuid primary key default gen_random_uuid(),
  question_id uuid not null references interview_questions(id) on delete cascade,
  answer_text text not null,
  answered_by text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists blueprints (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references organizations(id) on delete cascade,
  process_id uuid references business_processes(id) on delete set null,
  blueprint_type text not null,
  title text not null,
  content text not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists implementation_tasks (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references organizations(id) on delete cascade,
  process_id uuid references business_processes(id) on delete set null,
  title text not null,
  description text not null,
  status text not null default 'draft',
  priority text not null default 'medium',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists knowledge_sources (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid references organizations(id) on delete cascade,
  source_type text not null,
  title text not null,
  path text,
  content jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create or replace trigger organizations_set_updated_at
before update on organizations
for each row execute function set_updated_at();

create or replace trigger departments_set_updated_at
before update on departments
for each row execute function set_updated_at();

create or replace trigger tools_set_updated_at
before update on tools
for each row execute function set_updated_at();

create or replace trigger tool_integrations_set_updated_at
before update on tool_integrations
for each row execute function set_updated_at();

create or replace trigger business_processes_set_updated_at
before update on business_processes
for each row execute function set_updated_at();

create or replace trigger process_steps_set_updated_at
before update on process_steps
for each row execute function set_updated_at();

create or replace trigger ai_transform_patterns_set_updated_at
before update on ai_transform_patterns
for each row execute function set_updated_at();

create or replace trigger findings_set_updated_at
before update on findings
for each row execute function set_updated_at();

create or replace trigger recommendations_set_updated_at
before update on recommendations
for each row execute function set_updated_at();

create or replace trigger interview_questions_set_updated_at
before update on interview_questions
for each row execute function set_updated_at();

create or replace trigger interview_answers_set_updated_at
before update on interview_answers
for each row execute function set_updated_at();

create or replace trigger blueprints_set_updated_at
before update on blueprints
for each row execute function set_updated_at();

create or replace trigger implementation_tasks_set_updated_at
before update on implementation_tasks
for each row execute function set_updated_at();

create or replace trigger knowledge_sources_set_updated_at
before update on knowledge_sources
for each row execute function set_updated_at();
