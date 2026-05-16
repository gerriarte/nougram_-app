# Backend Specification: Quotes & Pipeline Module

**Version:** 1.0
**Date:** 2026-01-25
**Scope:** Data modeling, API contract, and business logic for the Quote Lifecycle.

---

## 1. Database Schema (SQLAlchemy Models)

### `quotes` Table

Core header table for proposals.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PK | Unique Identifier |
| `tenant_id` | UUID | FK | Multi-tenancy isolation |
| `project_name` | String(255) | Not Null | |
| `client_name` | String(255) | Not Null | |
| `client_email` | String(255) | Index | For CRM lookups |
| `status` | Enum | Index | `DRAFT`, `SENT`, `VIEWED`, `ACCEPTED`, `REJECTED`, `EXPIRED` |
| `version` | Integer | Default 1 | For tracking revisions |
| `currency` | char(3) | Default 'COP' | |
| `total_amount` | Decimal(18,2) | Not Null | Client Price (Before Tax) |
| `total_tax` | Decimal(18,2) | Not Null | |
| `total_cost` | Decimal(18,2) | Not Null | Internal BCR Cost |
| `margin_amount` | Decimal(18,2) | Generated | `total_amount - total_tax - total_cost` |
| `margin_percent` | Decimal(5,2) | | |
| `valid_until` | DateTime | | Expiration date |
| `created_by` | UUID | FK | User who created it |
| `created_at` | DateTime | Auto Now | |
| `updated_at` | DateTime | Auto upd | |

### `quote_items` Table

Line items for each quote.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PK | |
| `quote_id` | UUID | FK | |
| `service_id` | Integer | FK | Reference to Service Catalog |
| `description` | Text | | Custom description override |
| `pricing_type` | Enum | | `HOURLY`, `FIXED`, `RECURRING` |
| `quantity` | Integer | Default 1 | |
| `unit_cost` | Decimal(18,2) | | Snapdragon of BCR at time of quote |
| `unit_price` | Decimal(18,2) | | |
| `total_price` | Decimal(18,2) | | `quantity * unit_price` |

---

## 2. API Endpoints (FastAPI)

### `POST /api/v1/quotes`

Create a new quote (Draft).

**Payload:**

```json
{
  "project_name": "New Website",
  "client_name": "Acme Corp",
  "items": [
    { "service_id": 1, "estimated_hours": 20, "margin_target": 0.4 }
  ]
}
```

**Logic:**

1. Validate Tenant.
2. Fetch current `BCR` (Frozen Snapshot).
3. Calculate Costs & Prices based on `items`.
4. Save with `status = DRAFT`.

### `PUT /api/v1/quotes/{id}`

Update an existing quote. Only allowed if status is `DRAFT` or `SENT` (creates v2 if Sent).

**Logic:**

1. If `status == VIEWED/ACCEPTED`, return 409 Conflict (Must clone/revision).
2. Recalculate financials.
3. Update DB.

### `PATCH /api/v1/quotes/{id}/status`

Update status (Drag & Drop in Pipeline).

**Payload:**

```json
{ "status": "SENT" }
```

**State Machine Logic:**

1. **Any -> DRAFT**: Not allowed if previously SENT (must create new version).
2. **DRAFT -> SENT**:
    - Validates all fields.
    - Generates PDF.
    - **Locks** `unit_cost` snapshot if not already locked.
3. **SENT -> VIEWED**:
    - Triggered by "Pixel" or Link click in email.
4. **SENT/VIEWED -> ACCEPTED**:
    - **Closes** the opportunity.
    - Triggers "Project Creation" workflow (Optional).
5. **SENT -> REJECTED**:
    - Requires `rejection_reason` (optional).

### `GET /api/v1/quotes`

List quotes for Dashboard.

**Filters:**

- `status`: "DRAFT,SENT"
- `client_name`: Search
- `date_range`.

**Response:**
Returns simplified objects for Kanban/List view.

### `GET /api/v1/quotes/{id}`

Get full details including items for the Editor.

---

## 3. Analytics & Reporting

### `GET /api/v1/analytics/dashboard`

Returns aggregated metrics for the Dashboard charts. Avoids fetching full quote lists.

**Query Params:**

- `start_date` (ISO Date)
- `end_date` (ISO Date)
- `currency` (Default 'COP')

**Response:**

```json
{
  "total_quoted": 125000000,
  "pipeline_value": 45000000,
  "win_rate": 35.5,
  "avg_margin": 42.0,
  "funnel": {
    "sent_count": 12,
    "sent_value": 45000000,
    "won_count": 5,
    "won_value": 25000000,
    "lost_count": 2
  },
  "net_income": 8500000 // Real Profit from Won Deals
}
```

**Implementation Note:**
Use Database Aggregations for performance. Do NOT load all objects into memory.

```sql
-- Example for Net Income (Won Deals)
SELECT SUM(total_amount - total_tax - total_cost) 
FROM quotes 
WHERE status = 'ACCEPTED' AND created_at BETWEEN :start AND :end
```

## 3. Business Logic & State Options

### Versioning (Snapshots)

We do not overwrite quotes once sent to client.

- If user edits a `SENT` quote -> System confirms "Create Version 2?".
- If confirmed -> Clones `quote` + `items` with `version = version + 1`, sets new ID, links to parent.
- Old quote marked `ARCHIVED` or kep as history.

### PDF Generation

- `POST /api/v1/quotes/{id}/generate-pdf` triggers a background job (Celery).
- Generates PDF using HTML Template + Jinja2.
- Uploads to S3.
- Returns Signed URL.

### BCR Locking

**Critical:** Upon creating a quote, the `unit_cost` must be stored as a fixed value. Future changes to the Agency's BCR (e.g. Payroll increase) MUST NOT affect historical quotes, only new ones.
