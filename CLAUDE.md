# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`spedy-api` is a Python integration layer for the [Spedy API](https://api.spedy.com.br/v1) — a Brazilian SaaS platform for fiscal automation (NF-e and NFS-e invoice issuance). The full API reference is in `llm.txt`.

## Environment Setup

This is a Python project. The `.gitignore` references UV, Poetry, and PDM — use whichever package manager is configured once dependencies are introduced.

## API Fundamentals (from `llm.txt`)

### Authentication
Every request requires the header `X-Api-Key: <key>`. Keys are per-company (CNPJ). The sandbox (`https://sandbox-api.spedy.com.br/v1`) requires separate registration and uses separate keys from production (`https://api.spedy.com.br/v1`).

### Emission Flow
Invoice issuance is **asynchronous**: POST → `status: enqueued` → Spedy transmits to SEFAZ/municipality → webhook notifies your system. Prefer webhooks over polling. Average authorization time is under 10 seconds.

### Two Emission Modes
- **Simplified** (`POST /v1/orders`): no CFOP/NCM/tax calculation required; Spedy handles configuration from its backoffice. Best for SaaS/e-commerce with uniform taxation.
- **Full** (`POST /v1/product-invoices` or `/v1/service-invoices`): caller provides complete tax data (ICMS, PIS, COFINS for NF-e; ISS/retentions for NFS-e). Required for ERPs with per-product tax variation.

### Key Concepts
- **`integrationId`** (max 36 chars): strongly recommended on all POST requests. Acts as an idempotency key — re-POSTing with the same `integrationId` updates the existing invoice instead of creating a duplicate. Use the natural ID from the source system (order ID, transaction ID).
- **`status`** vs **`processingDetail.status`**: `status` is the invoice state (`enqueued`, `authorized`, `rejected`, `canceled`). `processingDetail.status: "success"` means the async job ran — not that the invoice was authorized. Check `processingDetail.message` and `.code` for rejection details; codes prefixed with `SPD` are Spedy-side validations.
- **Order ≠ Invoice**: an Order (`/v1/orders`) is an emission trigger. `autoIssueMode` controls when emission fires (`immediately`, `afterPayment`, `afterWarrency`, `disabled`).
- **City objects**: prefer `{ "city": { "code": "<ibge_code>" } }` over name+state when IBGE codes are available.

### Rate Limits
60 requests/minute, 5 requests/second, per API key. Headers `x-rate-limit-remaining` and `x-rate-limit-reset` are returned on every response.

### Webhooks
Spedy POSTs to your URL on events: `invoice.authorized`, `invoice.canceled`, `invoice.rejected`, `invoice.status_changed`. Payload shape: `{ "id": "<event-uuid>", "event": "<event-name>", "data": { ... } }`.

### Cancellation Nuances
- NF-e within legal window → cancels normally.
- NF-e outside window → may auto-generate a return NF-e (devolução).
- NFS-e outside window → depends on municipality; usually not possible.
- Always verify invoice `status` after attempting cancellation — canceling the order does not guarantee the invoice is canceled.
