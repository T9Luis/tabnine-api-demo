# Tabnine API Spec Discrepancies Report

**Spec version reviewed:** unified-tabnine-api.yaml v6.2.0  
**Source:** https://raw.githubusercontent.com/codota/t9-api-yamls/refs/heads/main/docs/unified-tabnine-api.yaml  
**Verified against:** Working client implementation (`tabnine_user_stats_fixed.py`)  
**Date:** 2026-06-05

---

## Summary

Three categories of issues were identified: parameters documented in the spec that do not match what the live API accepts, endpoints marked as deprecated without any replacement migration path in the spec itself, and parameters missing from the spec that are required by the live API.

---

## 1. Agent-Usage Endpoints — Wrong Parameter Names

**Affected endpoints:**
- `GET /api/v1/organization/agent-usage`
- `GET /api/v1/team/agent-usage`
- `GET /api/v1/user/agent-usage`

**What the spec documents:**

```yaml
parameters:
  - name: startDate
    in: query
    required: true
    schema:
      type: string
      format: date-time
  - name: endDate
    in: query
    required: true
    schema:
      type: string
      format: date-time
```

**What the live API actually accepts:**

```
from=2026-01-01T00:00:00Z
to=2026-03-31T00:00:00Z
```

Using `startDate`/`endDate` as documented returns a `500 Internal Server Error` with message `"Error trying to get organization agent usage"`. Using `from`/`to` works correctly.

**Impact:** Any client built strictly from the spec will receive a 500 on all three agent-usage endpoints.

---

## 2. Agent-Usage Endpoints — Missing Required Parameter

**Affected endpoints:**
- `GET /api/v1/organization/agent-usage`
- `GET /api/v1/team/agent-usage`
- `GET /api/v1/user/agent-usage`

**What the spec documents:** No `organizationId` parameter listed on any of these three endpoints. The spec implies the organization is inferred from the bearer token.

**What the live API actually requires:**

```
organizationId=<uuid>   # required query parameter
```

Omitting `organizationId` returns `401 Unauthorized` with message `"Unauthorized: Invalid organization."` — not a token problem, a missing parameter problem.

**Impact:** Any client built from the spec will receive a 401 on every agent-usage call, with a misleading error message that suggests an authentication issue rather than a missing parameter.

---

## 3. Agent-Usage Endpoints — Datetime Format Restriction Undocumented

**Affected endpoints:** All three agent-usage endpoints above.

**What the spec documents:** `format: date-time` — standard ISO 8601, which permits milliseconds (e.g. `2026-01-01T00:00:00.000Z`).

**What the live API actually requires:** Datetime strings must not include milliseconds. The format `%Y-%m-%dT%H:%M:%SZ` is required. Strings with milliseconds are rejected.

**Impact:** Clients generating timestamps programmatically (e.g. `new Date().toISOString()` in JavaScript, or `datetime.utcnow().isoformat()` in Python) will produce millisecond-precision strings that the API rejects, with no clear error message explaining why.

**Suggested fix:** Add a note to the parameter description:

```yaml
description: >
  Start of the reporting window (inclusive), ISO 8601 datetime.
  Must not include sub-second precision (e.g. 2026-01-01T00:00:00Z).
```

---

## 4. Misleading Server Note on Agent-Usage Section

**What the spec says:**

```yaml
# Note: The source spec for these endpoints specifies https://api.tabnine.com as the server.
# These endpoints are served from that host; the global server list is unchanged.
/api/v1/organization/agent-usage:
```

**Reality:** The agent-usage endpoints are served from `https://console.tabnine.com` — the same host as every other endpoint. The comment implies a different host, which is incorrect and caused significant integration confusion during testing.

**Suggested fix:** Remove or correct this comment. If these endpoints were historically on `api.tabnine.com`, document the migration explicitly.

---

## 5. v1 Usage Endpoints Marked Deprecated — No Migration Timeline or Sunset Date

**Affected endpoints:**
- `GET /api/v1/organization/usage` — `deprecated: true`
- `GET /api/v1/team/usage` — `deprecated: true`
- `GET /api/v1/user/usage` — `deprecated: true`

**What the spec says:**

> ⚠️ LEGACY ENDPOINT — DO NOT USE FOR NEW INTEGRATIONS. As of Tabnine 6.2, this endpoint only returns historical usage data collected before 6.2. It does not contain any activity from 6.2 onward and will never be updated with new data.

**Issues with the deprecation notice:**
- No sunset date is specified. Clients cannot plan removal.
- No `Sunset` or `Deprecation` HTTP response header is mentioned.
- The spec marks them `deprecated: true` but does not surface this in the HTML docs visible to users.
- Clients who built against v1 usage before 6.2 will silently receive incomplete data with no indication that new activity is missing.

**Suggested additions:**
1. Add a `Sunset` date to the spec and the response headers.
2. Add a `Warning` response header (per RFC 7234) on deprecated endpoints so clients receive machine-readable notice.
3. Document the exact Tabnine version that introduced 6.2 so clients can correlate the data cutoff date.

---

## 6. Audit Logs Endpoint — Parameters Missing from Public Docs

**Endpoint:** `GET /api/v1/organization/audit-logs`

**Parameters in the spec that are not surfaced in the public HTML documentation:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `from` | date-time | No | Start of time range |
| `to` | date-time | No | End of time range |
| `eventType` | string | No | Filter by event type (e.g. `team_member.added`) |
| `actorId` | string | No | Filter by actor UUID |
| `actorEmail` | email | No | Filter by actor email address |
| `resourceType` | string | No | Filter by `team`, `user`, `role`, or `organization` |
| `resourceId` | string | No | Filter by resource UUID |
| `sort` | enum `asc\|desc` | No | Sort order by timestamp, default `desc` |
| `format` | enum `json\|csv` | No | Output format — `csv` returns `text/csv` binary |

The public docs page only shows `limit` and `offset`. The seven filter parameters and the CSV export capability are not mentioned anywhere in the user-facing documentation, making them effectively invisible to integrators.

**Impact:** Integrators cannot filter audit logs by actor, event type, or time range without reading the raw YAML spec. The CSV export feature is entirely unknown.

---

## 7. `granularity` Parameter — Enum Values Inconsistent

**Spec definition (in `components/parameters`):**

```yaml
granularity:
  schema:
    type: string
    enum: [all, day, week, month, daily, weekly, monthly]
```

**What the spec documents on individual endpoints:**
The per-endpoint descriptions say `"e.g., all, day, week, month"` — using the short forms.

**What the working client uses:** `all`, `daily`, `weekly`, `monthly` — the long forms.

The enum in the shared component definition includes both short and long forms (`day` and `daily`, `week` and `weekly`, `month` and `monthly`), but it is unclear which set is actually accepted by each endpoint. There is no documentation of which forms map to which endpoints or whether both are equivalent aliases.

**Suggested fix:** Document explicitly which values are accepted per endpoint, or confirm both short and long forms are aliases and update all per-endpoint examples to use a single consistent set.

---

## 8. Duplicate User Endpoint Paths

The spec defines two paths that both retrieve user information:

| Path | Operation ID | Description |
|---|---|---|
| `GET /api/user/v1/{userId}` | `getUser` | Get user details including allowed teams |
| `GET /api/v1/user/{userId}` | `getUserInfo` | "User-level info (alternate path)" |

The second is described only as "alternate path" with no explanation of when to use one over the other, whether they return the same schema, or which is canonical. The response schemas are different (`GetUserResponse` vs `UserInfoResponse`).

**Suggested fix:** Clarify which path is canonical, whether one is deprecated, and document the difference in response schemas.

---

## 9. `GET /api/v1/organization/users` — Missing `organizationId` Parameter

**What the spec documents:** Only `limit` and `offset` as query parameters.

**What the live API requires:**

```
offset=0
limit=50
organizationId=<uuid>   # required — omitting returns 400 Validation Error
```

The response to a missing `organizationId` is:

```json
{
  "error": {
    "message": "Validation Error",
    "errors": ["offset: Expected number, received nan", "limit: Expected number, received nan"],
    "status": 400
  }
}
```

The error message is misleading — it reports `offset` and `limit` as invalid rather than identifying the missing `organizationId`.

**Impact:** Two bugs in one: the spec omits a required parameter, and the API returns a misleading error message when it is missing.

---

## Recommended Priority

| # | Issue | Severity | Effort to fix |
|---|---|---|---|
| 1 | Agent-usage wrong param names (`startDate`/`endDate` vs `from`/`to`) | **Critical** | Low — rename in spec |
| 2 | Agent-usage missing required `organizationId` | **Critical** | Low — add to spec |
| 9 | List Users missing required `organizationId` | **Critical** | Low — add to spec |
| 3 | Datetime milliseconds rejection undocumented | **High** | Low — add note to description |
| 4 | Misleading server host comment on agent-usage | **High** | Low — remove/correct comment |
| 6 | Audit logs filter params not in public docs | **Medium** | Medium — update public docs page |
| 7 | `granularity` enum inconsistency | **Medium** | Low — standardise enum |
| 8 | Duplicate user endpoint paths unexplained | **Medium** | Medium — add clarification |
| 5 | Deprecated v1 usage — no sunset date | **Low** | Medium — define timeline |
