# AGENTS.md

This repository uses `product-prd.md` as the primary product requirements document.

## Start-of-work rule

Before making plans, code changes, schema updates, API changes, or UI changes, read:

1. `/Users/kazuhiko/Documents/AI BizOps Orchestrator/product-prd.md`
2. This file

Treat `product-prd.md` as the source of truth for product scope and requirements.

## Mandatory working style

Before starting any meaningful work, always create a plan first.

The plan must:
- break the work into understandable steps
- show the intended order of execution
- be shared in a user-understandable way
- start with the big picture before diving into implementation detail

When presenting a plan, prefer this explanation order:
- overall picture
- meaning of important technical terms
- comparison of realistic options
- recommended choice and why it was selected

For each task, and especially when a task is completed, always explain:
- what was planned
- what was executed
- what result was produced
- why that result matters

These explanations must be understandable to:
- beginners
- non-engineers

When technical terms are used, add a short plain-language explanation.

Do not assume the user already knows engineering vocabulary.
Explain terms such as monorepo, CRUD, API, backend, frontend, schema, migration, and framework in simple Japanese when they first matter.

For major technical choices, always explain:
- what it is
- why it is needed
- realistic alternatives
- advantages
- disadvantages
- why this choice is recommended for this project now

Primary emphasis should be on explanation and decision-making rationale.
Fine-grained configuration details should be treated as supplemental context, not the main explanation.

Treat the user as a PM aiming to become a full-stack engineer.
Act as a lead engineer who not only makes decisions, but also teaches the reasoning behind them.

## Product intent

The core objective is not just SaaS integration or workflow chat assistance.

The product must help re-architect internal operations and SaaS usage into a more optimal system that improves:

- PL
- BS
- ROI
- operational efficiency
- decision speed

## Build priority

Implement in this order unless the user explicitly overrides it:

1. DB and CRUD
2. natural language decomposition
3. rule-based diagnosis
4. Gemini generation
5. visualization
6. Slack question generation
7. n8n draft generation
8. UI improvements

## Required architecture direction

Use the following internal responsibility split, implemented as services/modules as appropriate:

1. Discovery Agent
2. Decomposition Agent
3. Diagnosis Agent
4. Recommendation Agent
5. Interview Agent
6. Blueprint Agent

These are internal architectural responsibilities, not necessarily separate deployed agents.

## Implementation guardrails

- Prefer a working end-to-end MVP over premature sophistication.
- Keep type definitions explicit.
- Use environment variables for Gemini, Supabase, and Slack configuration.
- Keep AI calls small by passing structured outputs rather than long raw text whenever possible.
- Use rule-based logic for deterministic judgments and aggregation.
- Do not implement production SaaS mutations or automatic live changes.
- Keep human approval in the loop for risky or external actions.
- Add basic error handling.
- Keep the UI simple and functional.
- Provide sample data and a README.

## Core stack

- Frontend: Next.js
- Backend: FastAPI
- Database: Supabase Postgres
- AI: Gemini API
- Notification: Slack Incoming Webhook
- Workflow draft output: n8n JSON
- Knowledge source: local Markdown / JSON

## Notes for future agents

- If there is any conflict between ad hoc implementation ideas and `product-prd.md`, follow `product-prd.md`.
- If requirements expand, update `product-prd.md` first, then implement.
