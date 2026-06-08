import re as _re
import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Tabnine API Demo",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Constants ──────────────────────────────────────────────────────────────────
BASE_URL = "https://console.tabnine.com"

DOCS_BASE = "https://docs.tabnine.com/main/administering-tabnine/managing-your-team/tabnine-apis"

# Each entry:
#   method       – HTTP verb
#   path         – URL path (may contain {placeholders})
#   version      – "v1" or "v2" (for display grouping)
#   category     – logical section label
#   description  – plain-English summary
#   doc_anchor   – fragment appended to DOCS_BASE for the docs link
#   path_params  – list of field names that live in the URL path
#   body_fields  – ordered list of (field_name, default_value, hint) for POST/PATCH body
#   query_params – list of (field_name, default_value, hint) added as query-string args
API_ENDPOINTS = {

    # ── v1 · Users ────────────────────────────────────────────────────────────

    "v1 · Get Organisation": {
        "method": "GET",
        "path": "/api/v1/organization",
        "version": "v1",
        "category": "Organisation",
        "description": "Retrieve details about your Tabnine organisation.",
        "doc_anchor": "#get-organisation",
        "path_params": [],
        "body_fields": [],
        "query_params": [],
    },
    "v1 · Get License": {
        "method": "GET",
        "path": "/api/v1/license",
        "version": "v1",
        "category": "Organisation",
        "description": "Retrieve your organisation licence details including seat counts and expiry.",
        "doc_anchor": "#get-license",
        "path_params": [],
        "body_fields": [],
        "query_params": [],
    },
    "v1 · List Users": {
        "method": "GET",
        "path": "/api/v1/organization/users",
        "version": "v1",
        "category": "Users",
        "description": "Retrieve a paginated list of all users in your Tabnine organisation.",
        "doc_anchor": "#list-users",
        "path_params": [],
        "body_fields": [],
        "query_params": [
            ("offset", "0",  "Pagination offset (0-based)"),
            ("limit",  "50", "Number of users to return (max 100)"),
        ],
    },
    # ── v1 · Users ────────────────────────────────────────────────────────────

    "v1 · List Team Users": {
        "method": "GET",
        "path": "/api/v1/team/{teamId}/users",
        "version": "v1",
        "category": "Users",
        "description": "List users in a specific team. Supports pagination via offset and limit query parameters.",
        "doc_anchor": "#list-team-users",
        "path_params": ["teamId"],
        "body_fields": [],
        "query_params": [
            ("offset", "0", "Pagination offset"),
            ("limit", "50", "Max results per page"),
        ],
    },

    # ── v1 · Teams ────────────────────────────────────────────────────────────

    "v1 · List Teams": {
        "method": "GET",
        "path": "/api/v1/organization/teams",
        "version": "v1",
        "category": "Teams",
        "description": "Retrieve all teams defined in your Tabnine organisation.",
        "doc_anchor": "#list-teams",
        "path_params": [],
        "body_fields": [],
        "query_params": [],
    },

    # ── v1 · Usage ────────────────────────────────────────────────────────────

    "v1 · Org Usage": {
        "method": "GET",
        "path": "/api/v1/organization/usage",
        "version": "v1",
        "category": "Usage",
        "description": "Organisation-wide usage report covering code completions, chat, and agent activity. Supports granularity: all, daily, weekly, or monthly.",
        "doc_anchor": "#org-usage",
        "path_params": [],
        "body_fields": [],
        "query_params": [
            ("organizationId", "", "Your organisation UUID"),
            ("from", "2026-01-01T00:00:00Z", "ISO 8601 start date"),
            ("to", "2026-03-31T00:00:00Z", "ISO 8601 end date"),
            ("granularity", "all", "all | daily | weekly | monthly"),
        ],
    },
    "v1 · Team Usage": {
        "method": "GET",
        "path": "/api/v1/team/usage",
        "version": "v1",
        "category": "Usage",
        "description": "Usage report scoped to a specific team. Same response shape as org usage.",
        "doc_anchor": "#team-usage",
        "path_params": [],
        "body_fields": [],
        "query_params": [
            ("organizationId", "", "Your organisation UUID"),
            ("teamId", "", "Team UUID"),
            ("from", "2026-01-01T00:00:00Z", "ISO 8601 start date"),
            ("to", "2026-03-31T00:00:00Z", "ISO 8601 end date"),
            ("granularity", "all", "all | daily | weekly | monthly"),
        ],
    },
    "v1 · User Usage": {
        "method": "GET",
        "path": "/api/v1/user/usage",
        "version": "v1",
        "category": "Usage",
        "description": "Usage report scoped to a specific user, including code completions, chat, and agent metrics.",
        "doc_anchor": "#user-usage",
        "path_params": [],
        "body_fields": [],
        "query_params": [
            ("organizationId", "", "Your organisation UUID"),
            ("userId", "", "User UUID"),
            ("from", "2026-01-01T00:00:00Z", "ISO 8601 start date"),
            ("to", "2026-03-31T00:00:00Z", "ISO 8601 end date"),
            ("granularity", "all", "all | daily | weekly | monthly"),
        ],
    },
    "v1 · Org Account Utilizations": {
        "method": "GET",
        "path": "/api/v1/organization/account-utilizations",
        "version": "v1",
        "category": "Usage",
        "description": "Retrieve seat and account utilisation statistics for your organisation.",
        "doc_anchor": "#org-account-utilizations",
        "path_params": [],
        "body_fields": [],
        "query_params": [],
    },
    "v1 · Team Account Utilizations": {
        "method": "GET",
        "path": "/api/v1/team/account-utilizations",
        "version": "v1",
        "category": "Usage",
        "description": "Retrieve seat and account utilisation statistics scoped to a specific team.",
        "doc_anchor": "#team-account-utilizations",
        "path_params": [],
        "body_fields": [],
        "query_params": [
            ("teamId", "", "Team UUID"),
        ],
    },

    # ── v1 · Agent Usage ──────────────────────────────────────────────────────

    "v1 · Org Agent Usage": {
        "method": "GET",
        "path": "/api/v1/organization/agent-usage",
        "version": "v1",
        "category": "Agent Usage",
        "description": "Retrieve agent (Tabnine Agent) usage statistics for your organisation.",
        "doc_anchor": "#org-agent-usage",
        "path_params": [],
        "body_fields": [],
        "query_params": [
            ("organizationId", "", "Your organisation UUID"),
            ("startDate", "2026-01-01T00:00:00Z", "ISO 8601 start date"),
            ("endDate", "2026-03-31T00:00:00Z", "ISO 8601 end date"),
        ],
    },
    "v1 · Team Agent Usage": {
        "method": "GET",
        "path": "/api/v1/team/agent-usage",
        "version": "v1",
        "category": "Agent Usage",
        "description": "Retrieve agent usage statistics scoped to a specific team.",
        "doc_anchor": "#team-agent-usage",
        "path_params": [],
        "body_fields": [],
        "query_params": [
            ("organizationId", "", "Your organisation UUID"),
            ("teamId", "", "Team UUID"),
            ("startDate", "2026-01-01T00:00:00Z", "ISO 8601 start date"),
            ("endDate", "2026-03-31T00:00:00Z", "ISO 8601 end date"),
        ],
    },
    "v1 · User Agent Usage": {
        "method": "GET",
        "path": "/api/v1/user/agent-usage",
        "version": "v1",
        "category": "Agent Usage",
        "description": "Retrieve agent usage statistics scoped to a specific user.",
        "doc_anchor": "#user-agent-usage",
        "path_params": [],
        "body_fields": [],
        "query_params": [
            ("organizationId", "", "Your organisation UUID"),
            ("userId", "", "User UUID"),
            ("startDate", "2026-01-01T00:00:00Z", "ISO 8601 start date"),
            ("endDate", "2026-03-31T00:00:00Z", "ISO 8601 end date"),
        ],
    },

    # ── v1 · Audit Log ────────────────────────────────────────────────────────

    "v1 · Audit Logs": {
        "method": "GET",
        "path": "/api/v1/organization/audit-logs",
        "version": "v1",
        "category": "Audit Log",
        "description": "Retrieve a paginated audit log of admin actions across your organisation.",
        "doc_anchor": "#audit-logs",
        "path_params": [],
        "body_fields": [],
        "query_params": [
            ("limit", "50", "Max results per page"),
            ("offset", "0", "Pagination offset"),
        ],
    },

    # ── v1 · Instance ─────────────────────────────────────────────────────────

    "v1 · Instance Permissions": {
        "method": "GET",
        "path": "/api/v1/instance/permissions",
        "version": "v1",
        "category": "Instance",
        "description": "Retrieve the permissions available for a given role in your Tabnine instance.",
        "doc_anchor": "#instance-permissions",
        "path_params": [],
        "body_fields": [],
        "query_params": [
            ("role", "Member", "Member or Admin"),
        ],
    },

    # ── user/v1 · User Management (newer namespace) ───────────────────────────

    "user/v1 · Get User by ID": {
        "method": "GET",
        "path": "/api/user/v1/{userId}",
        "version": "v1",
        "category": "User Management",
        "description": "Retrieve full details for a specific user by their UUID, including role, status, and team memberships.",
        "doc_anchor": "#get-user-by-id",
        "path_params": ["userId"],
        "body_fields": [],
        "query_params": [],
    },
    "user/v1 · Get User by Email": {
        "method": "GET",
        "path": "/api/user/v1/by-email/{email}",
        "version": "v1",
        "category": "User Management",
        "description": "Retrieve full details for a specific user by their email address.",
        "doc_anchor": "#get-user-by-email",
        "path_params": ["email"],
        "body_fields": [],
        "query_params": [],
    },
    "user/v1 · Update User": {
        "method": "PATCH",
        "path": "/api/user/v1/{userId}",
        "version": "v1",
        "category": "User Management",
        "description": "Partially update a user's profile. All fields are optional. Cannot modify self, instance admins, or anonymised users.",
        "doc_anchor": "#update-user",
        "path_params": ["userId"],
        "body_fields": [
            ("role",   "Member", "Member or Admin"),
            ("active", "true",   "true or false"),
        ],
        "query_params": [],
    },
    "user/v1 · Get User Allowed Teams": {
        "method": "GET",
        "path": "/api/user/v1/{userId}/allowed-teams",
        "version": "v1",
        "category": "User Management",
        "description": "Retrieve the list of teams a user is allowed to access.",
        "doc_anchor": "#get-user-allowed-teams",
        "path_params": ["userId"],
        "body_fields": [],
        "query_params": [],
    },
    "user/v1 · Set User Allowed Teams": {
        "method": "PATCH",
        "path": "/api/user/v1/{userId}/allowed-teams",
        "version": "v1",
        "category": "User Management",
        "description": "Replace the set of teams a user is allowed to access. Send an array of team UUIDs.",
        "doc_anchor": "#set-user-allowed-teams",
        "path_params": ["userId"],
        "body_fields": [
            ("teamIds", '["team-uuid-here"]', "JSON array of team UUIDs"),
        ],
        "query_params": [],
    },
    "user/v1 · Remove User Allowed Teams": {
        "method": "DELETE",
        "path": "/api/user/v1/{userId}/allowed-teams",
        "version": "v1",
        "category": "User Management",
        "description": "Remove one or more teams from a user's allowed-teams list. Send the team UUIDs to remove.",
        "doc_anchor": "#remove-user-allowed-teams",
        "path_params": ["userId"],
        "body_fields": [
            ("teamIds", '["team-uuid-here"]', "JSON array of team UUIDs to remove"),
        ],
        "query_params": [],
    },

    # ── team/v1 · Team Management (newer namespace) ───────────────────────────

    "team/v1 · Get Team": {
        "method": "GET",
        "path": "/api/team/v1/{teamId}",
        "version": "v1",
        "category": "Team Management",
        "description": "Retrieve details for a specific team by its UUID.",
        "doc_anchor": "#get-team",
        "path_params": ["teamId"],
        "body_fields": [],
        "query_params": [],
    },
    "team/v1 · Create Team": {
        "method": "POST",
        "path": "/api/team/v1",
        "version": "v1",
        "category": "Team Management",
        "description": "Create a new team in your Tabnine organisation. Requires Admin role.",
        "doc_anchor": "#create-team",
        "path_params": [],
        "body_fields": [
            ("name", "My New Team", "Team display name"),
        ],
        "query_params": [],
    },
    "team/v1 · Update Team": {
        "method": "PUT",
        "path": "/api/team/v1/{teamId}",
        "version": "v1",
        "category": "Team Management",
        "description": "Update an existing team's name or settings. Requires Admin or Manager role.",
        "doc_anchor": "#update-team",
        "path_params": ["teamId"],
        "body_fields": [
            ("name", "", "New team display name"),
        ],
        "query_params": [],
    },

    # ── team/v1 · Repository Connections ──────────────────────────────────────

    "team/v1 · List Repo Connections": {
        "method": "GET",
        "path": "/api/team/v1/{teamId}/connections/repositories",
        "version": "v1",
        "category": "Repo Connections",
        "description": "List all repository connections for a specific team (used by Tabnine Context Engine).",
        "doc_anchor": "#list-repo-connections",
        "path_params": ["teamId"],
        "body_fields": [],
        "query_params": [],
    },
    "team/v1 · Add Repo Connection": {
        "method": "POST",
        "path": "/api/team/v1/{teamId}/connections/repositories",
        "version": "v1",
        "category": "Repo Connections",
        "description": "Add a repository connection to a team. Idempotent operation.",
        "doc_anchor": "#add-repo-connection",
        "path_params": ["teamId"],
        "body_fields": [
            ("repository_link",                 "https://github.com/org/repo", "Full repository URL"),
            ("repo_type",                       "git",                         "git or other"),
            ("authentication_method",           "ssh",                         "ssh or https"),
            ("authentication_credentials_name", "",                            "Credential name (optional)"),
            ("view_source_link_pattern",        "",                            "Source link pattern (optional)"),
        ],
        "query_params": [],
    },
    "team/v1 · Update Repo Connection": {
        "method": "PUT",
        "path": "/api/team/v1/{teamId}/connections/repositories/{repositoryLink}",
        "version": "v1",
        "category": "Repo Connections",
        "description": "Update an existing repository connection for a team.",
        "doc_anchor": "#update-repo-connection",
        "path_params": ["teamId", "repositoryLink"],
        "body_fields": [
            ("repo_type",                       "git",  "git or other"),
            ("authentication_method",           "ssh",  "ssh or https"),
            ("authentication_credentials_name", "",     "Credential name (optional)"),
            ("view_source_link_pattern",        "",     "Source link pattern (optional)"),
        ],
        "query_params": [],
    },
    "team/v1 · Delete Repo Connection": {
        "method": "DELETE",
        "path": "/api/team/v1/{teamId}/connections/repositories/{repositoryLink}",
        "version": "v1",
        "category": "Repo Connections",
        "description": "Remove a repository connection from a team.",
        "doc_anchor": "#delete-repo-connection",
        "path_params": ["teamId", "repositoryLink"],
        "body_fields": [],
        "query_params": [],
    },

    # ── invitation/v1 · Invitations ───────────────────────────────────────────

    "invitation/v1 · List Invitations": {
        "method": "GET",
        "path": "/api/invitation/v1",
        "version": "v1",
        "category": "Invitations",
        "description": "Retrieve a paginated list of pending and historical invitations for your organisation.",
        "doc_anchor": "#list-invitations",
        "path_params": [],
        "body_fields": [],
        "query_params": [
            ("offset", "0",  "Pagination offset"),
            ("limit",  "50", "Max results per page"),
        ],
    },
    "invitation/v1 · Create Invitation": {
        "method": "POST",
        "path": "/api/invitation/v1",
        "version": "v1",
        "category": "Invitations",
        "description": "Invite a user to your Tabnine organisation by email. Optionally assign them to a team and role.",
        "doc_anchor": "#create-invitation",
        "path_params": [],
        "body_fields": [
            ("email",  "", "Email address of the person to invite"),
            ("teamId", "", "Team UUID to assign (optional)"),
            ("role",   "Member", "Member or Admin"),
        ],
        "query_params": [],
    },

    # ── v2 · Usage ────────────────────────────────────────────────────────────

    "v2 · Org Usage": {
        "method": "GET",
        "path": "/api/v2/organization/usage",
        "version": "v2",
        "category": "Usage",
        "description": "Enhanced org-wide usage report (v2). Includes activeUsers, totalTokensConsumed, totalInputTokens, totalOutputTokens, totalCost, and a per-model breakdown.",
        "doc_anchor": "#org-usage-v2",
        "path_params": [],
        "body_fields": [],
        "query_params": [
            ("organizationId", "", "Your organisation UUID"),
            ("from", "2026-01-01T00:00:00Z", "ISO 8601 start date"),
            ("to", "2026-03-31T00:00:00Z", "ISO 8601 end date"),
            ("granularity", "all", "all | daily | weekly | monthly"),
        ],
    },
    "v2 · Team Usage": {
        "method": "GET",
        "path": "/api/v2/team/usage",
        "version": "v2",
        "category": "Usage",
        "description": "Enhanced team-scoped usage report (v2). Same shape as v2 org usage but filtered to a teamId.",
        "doc_anchor": "#team-usage-v2",
        "path_params": [],
        "body_fields": [],
        "query_params": [
            ("organizationId", "", "Your organisation UUID"),
            ("teamId", "", "Team UUID"),
            ("from", "2026-01-01T00:00:00Z", "ISO 8601 start date"),
            ("to", "2026-03-31T00:00:00Z", "ISO 8601 end date"),
            ("granularity", "all", "all | daily | weekly | monthly"),
        ],
    },
    "v2 · User Usage": {
        "method": "GET",
        "path": "/api/v2/user/usage",
        "version": "v2",
        "category": "Usage",
        "description": "Enhanced user-scoped usage report (v2). Includes code completions, chat messages, agent interactions, and per-model token counts.",
        "doc_anchor": "#user-usage-v2",
        "path_params": [],
        "body_fields": [],
        "query_params": [
            ("organizationId", "", "Your organisation UUID"),
            ("userId", "", "User UUID"),
            ("from", "2026-01-01T00:00:00Z", "ISO 8601 start date"),
            ("to", "2026-03-31T00:00:00Z", "ISO 8601 end date"),
            ("granularity", "all", "all | daily | weekly | monthly"),
        ],
    },
}

# ── Helpers ────────────────────────────────────────────────────────────────────

def make_request(
    token: str,
    method: str,
    path: str,
    body: dict | None = None,
    base_url: str = BASE_URL,
    query_params: dict | None = None,
) -> tuple[int, dict]:
    """Execute an authenticated request against the Tabnine API."""
    url = f"{base_url}{path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    try:
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=body if body else None,
            params=query_params,   # requests handles URL-encoding (@ → %40 etc.)
            timeout=15,
        )
        try:
            data = response.json()
        except Exception:
            data = {"raw": response.text}
        return response.status_code, data
    except requests.exceptions.ConnectionError:
        return 0, {"error": "Connection error — check your network or the API base URL."}
    except requests.exceptions.Timeout:
        return 0, {"error": "Request timed out after 15 seconds."}


def status_badge(code: int) -> str:
    """Return a coloured Markdown badge string for an HTTP status code."""
    if code == 0:
        return "🔴 **No response**"
    if 200 <= code < 300:
        return f"🟢 **{code} OK**"
    if 400 <= code < 500:
        return f"🟡 **{code} Client Error**"
    return f"🔴 **{code} Server Error**"


def build_path(path_template: str, params: dict) -> str:
    """Replace path-level placeholders like {email} with actual values."""
    for key, val in params.items():
        path_template = path_template.replace(f"{{{key}}}", val)
    return path_template


# ── Pre-fetch helpers (results cached in session_state per token) ───────────────

def _fetch_teams(token: str, base_url: str) -> list[dict]:
    cache_key = f"_teams_{hash(token + base_url)}"
    if cache_key not in st.session_state:
        org_id = st.session_state.get("org_id") or None
        qp: dict = {"offset": 0, "limit": 200}
        if org_id:
            qp["organizationId"] = org_id
        code, data = make_request(token, "GET", "/api/v1/organization/teams", base_url=base_url, query_params=qp)
        if code == 200:
            if isinstance(data, list):
                teams = data
            elif isinstance(data, dict):
                teams = next(
                    (data[k] for k in ("teams", "data", "items") if isinstance(data.get(k), list)),
                    [],
                )
            else:
                teams = []
        else:
            teams = []
        st.session_state[cache_key] = teams
    return st.session_state[cache_key]


def _fetch_users(token: str, base_url: str, force: bool = False) -> list[dict]:
    """Fetch all org users and cache them. Returns a flat list of user dicts."""
    cache_key = f"_users_{hash(token + base_url)}"
    if force and cache_key in st.session_state:
        del st.session_state[cache_key]

    if cache_key not in st.session_state:
        org_id = st.session_state.get("org_id") or None
        qp: dict = {"offset": 0, "limit": 200}
        if org_id:
            qp["organizationId"] = org_id
        code, data = make_request(token, "GET", "/api/v1/organization/users", base_url=base_url, query_params=qp)
        users: list[dict] = []
        if code == 200:
            if isinstance(data, list):
                # Plain array response
                users = data
            elif isinstance(data, dict):
                # Try every known wrapper key
                for key in ("users", "data", "items", "members", "results"):
                    val = data.get(key)
                    if isinstance(val, list):
                        users = val
                        break
                # Some endpoints nest the user under a "user" sub-key in each item
                if not users and "user" in data and isinstance(data["user"], dict):
                    users = [data["user"]]
        # Normalise: ensure each entry has at minimum an 'id' and 'email' field
        normalised = []
        for u in users:
            if isinstance(u, dict):
                # Some responses wrap the user under a "user" key inside each list item
                actual = u.get("user", u)
                uid   = actual.get("id") or actual.get("user_id") or actual.get("userId") or ""
                email = actual.get("email") or actual.get("username") or uid
                role  = actual.get("role", "")
                active = actual.get("active", True)
                normalised.append({
                    "id": uid,
                    "email": email,
                    "role": role,
                    "active": active,
                    "_raw": actual,
                })
        st.session_state[cache_key] = normalised
        # Store last fetch status for UI feedback
        st.session_state[f"{cache_key}_status"] = code

    return st.session_state[cache_key]


# ── Smart parameter input dispatcher ───────────────────────────────────────────

def _smart_param_input(
    key: str,
    default: str,
    hint: str,
    widget_key: str,
    token: str | None = None,
    base_url: str = BASE_URL,
    required: bool = False,
) -> str:
    """Render the most appropriate Streamlit widget for a given parameter key."""
    label = key.replace("_", " ").title() + (" *" if required else "")
    kl    = key.lower()

    # ── Organisation ID — auto-filled, read-only ───────────────────────────
    if kl == "organizationid":
        st.text_input(
            label,
            value=default,
            key=widget_key,
            help="Auto-filled from your verified token.",
            disabled=True,
        )
        return default

    # ── Date / time range fields → calendar picker ─────────────────────────
    if kl in ("from", "to", "startdate", "enddate"):
        # Parse the default ISO string to a Python date
        parsed_date = None
        for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
            try:
                parsed_date = datetime.strptime(default, fmt).date()
                break
            except (ValueError, TypeError):
                continue
        if parsed_date is None:
            parsed_date = datetime.today().date()

        picked = st.date_input(label, value=parsed_date, help=hint, key=widget_key)
        return picked.strftime("%Y-%m-%dT00:00:00Z")

    # ── Granularity → segmented selectbox ─────────────────────────────────
    if kl == "granularity":
        options = ["all", "daily", "weekly", "monthly"]
        idx = options.index(default) if default in options else 0
        return st.selectbox(label, options=options, index=idx, help=hint, key=widget_key)

    # ── Role → selectbox ───────────────────────────────────────────────────
    if kl == "role":
        options = ["Member", "Admin"]
        idx = options.index(default) if default in options else 0
        return st.selectbox(label, options=options, index=idx, help=hint, key=widget_key)

    # ── Team ID → pre-fetched team selector ───────────────────────────────
    if kl == "teamid" and token:
        teams = _fetch_teams(token, base_url)
        if teams:
            # Build label → id map
            options_map: dict[str, str] = {}
            for t in teams:
                tid  = t.get("id", "")
                name = t.get("name", tid)
                flag = " (default)" if t.get("isDefaultTeam") else ""
                options_map[f"{name}{flag}"] = tid

            labels = list(options_map.keys())
            # Try to pre-select if default is a known UUID
            pre = next((lbl for lbl, v in options_map.items() if v == default), labels[0])
            chosen = st.selectbox(label, options=labels,
                                  index=labels.index(pre), help=hint, key=widget_key)
            st.caption(f"ID: `{options_map[chosen]}`")
            return options_map[chosen]
        # Fallback if fetch failed
        return st.text_input(label, value=default, help=hint,
                             key=widget_key, placeholder="Team UUID")

    # ── User ID → pre-fetched user selector ───────────────────────────────
    if kl in ("userid", "user_id") and token:
        cache_key    = f"_users_{hash(token + base_url)}"
        refresh_key  = f"_refresh_users_{widget_key}"

        # Refresh button sits on the same row as the label via a trick column
        hdr_col, btn_col = st.columns([4, 1])
        with hdr_col:
            st.markdown(f"**{label}**", help=hint)
        with btn_col:
            if st.button("↻ Refresh", key=refresh_key, help="Re-fetch the user list"):
                _fetch_users(token, base_url, force=True)

        users = _fetch_users(token, base_url)
        fetch_status = st.session_state.get(f"{cache_key}_status", None)

        if fetch_status is not None and fetch_status != 200:
            st.warning(
                f"Could not load users (HTTP {fetch_status}). "
                "Paste the User UUID manually below."
            )
            return st.text_input(
                "User Id (manual)",
                value=default,
                key=widget_key,
                placeholder="User UUID",
            )

        if not users:
            st.info("No users found in this organisation, or the list is still loading.")
            return st.text_input(
                "User Id (manual)",
                value=default,
                key=widget_key,
                placeholder="User UUID",
            )

        options_map: dict[str, str] = {}
        for u in users:
            uid    = u.get("id", "")
            email  = u.get("email", uid)
            role   = u.get("role", "")
            status = "✅" if u.get("active", True) else "❌"
            options_map[f"{status} {email}  ({role})"] = uid

        labels = list(options_map.keys())
        pre    = next((lbl for lbl, v in options_map.items() if v == default), labels[0])
        chosen = st.selectbox(
            "Select user",
            options=labels,
            index=labels.index(pre) if pre in labels else 0,
            key=widget_key,
            label_visibility="collapsed",
        )
        chosen_id = options_map[chosen]
        st.caption(f"User ID: `{chosen_id}` · {len(users)} user{'s' if len(users) != 1 else ''} loaded")
        return chosen_id

    # ── Limit / Offset → number input ─────────────────────────────────────
    if kl in ("limit", "offset"):
        try:
            default_int = int(default)
        except (ValueError, TypeError):
            default_int = 0
        step = 10 if kl == "limit" else 1
        val  = st.number_input(label, min_value=0, max_value=1000,
                               value=default_int, step=step, help=hint, key=widget_key)
        return str(int(val))

    # ── Default: plain text input ──────────────────────────────────────────
    return st.text_input(label, value=default, help=hint, key=widget_key)


# ── Value type detection & formatting ──────────────────────────────────────────

# Keywords that signal a field holds a timestamp
_TS_KEYS = {"expir", "creat", "updat", "revok", "at", "date", "time", "issued", "start", "end"}
# Keywords that signal a cost / monetary value
_COST_KEYS = {"cost", "price", "amount", "fee", "spend"}
# Keywords that signal a seat / count of something
_SEAT_KEYS = {"seat", "count", "total", "used", "limit", "quota", "active"}
# UUID pattern (simple heuristic)
_UUID_RE = _re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", _re.I)


def _is_ts_key(key: str) -> bool:
    kl = key.lower()
    return any(kw in kl for kw in _TS_KEYS)


def _fmt_ts(value) -> str | None:
    """Try to parse value as a timestamp and return a human date string, or None."""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        # Unix seconds (~2001–2286) or milliseconds
        if 1_000_000_000 < value < 9_999_999_999:
            return datetime.utcfromtimestamp(value).strftime("%-d %b %Y  %H:%M UTC")
        if 1_000_000_000_000 < value < 9_999_999_999_999:
            return datetime.utcfromtimestamp(value / 1000).strftime("%-d %b %Y  %H:%M UTC")
    if isinstance(value, str):
        for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ",
                    "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
            try:
                return datetime.strptime(value, fmt).strftime("%-d %b %Y  %H:%M UTC")
            except ValueError:
                continue
    return None


def _classify(key: str, value) -> tuple[str, str]:
    """Return (display_string, type_tag) for a single field."""
    kl = key.lower()

    if value is None:
        return "—", "null"

    if isinstance(value, bool):
        return ("Yes" if value else "No"), ("bool_true" if value else "bool_false")

    if isinstance(value, list):
        return f"{len(value)} item{'s' if len(value) != 1 else ''}", "list"

    if isinstance(value, dict):
        return f"{len(value)} field{'s' if len(value) != 1 else ''}", "dict"

    # Timestamp fields
    if _is_ts_key(key):
        ts = _fmt_ts(value)
        if ts:
            return ts, "date"

    if isinstance(value, (int, float)):
        # Cost / monetary
        if any(kw in kl for kw in _COST_KEYS):
            return f"${value:,.2f}", "cost"
        # Ratio / factor (0–1 or 0–100 labelled as factor/rate/percent)
        if any(kw in kl for kw in ("factor", "rate", "percent", "ratio")) and 0 <= value <= 1:
            return f"{value * 100:.1f}%", "percent"
        return f"{int(value):,}" if isinstance(value, int) else f"{value:,.4f}", "number"

    if isinstance(value, str):
        if _UUID_RE.match(value):
            return value, "uuid"
        # ISO datetime as string (fallback)
        ts = _fmt_ts(value)
        if ts:
            return ts, "date"
        return value, "string"

    return str(value), "other"


# ── Single-field HTML card ──────────────────────────────────────────────────────

_CARD_COLOURS = {
    "date":       "#3B82F6",   # blue
    "bool_true":  "#10B981",   # green
    "bool_false": "#EF4444",   # red
    "cost":       "#F59E0B",   # amber
    "percent":    "#8B5CF6",   # violet
    "number":     "#6366F1",   # indigo
    "uuid":       "#64748B",   # slate
    "list":       "#0EA5E9",   # sky
    "dict":       "#0EA5E9",
    "null":       "#374151",   # dark grey
    "string":     "#475569",   # cool grey
    "other":      "#475569",
}

_BOOL_ICONS = {"bool_true": "✅", "bool_false": "❌"}


def _field_card_html(label: str, display: str, type_tag: str) -> str:
    colour = _CARD_COLOURS.get(type_tag, "#475569")
    icon   = _BOOL_ICONS.get(type_tag, "")
    font   = "font-family:monospace;font-size:0.78rem;" if type_tag == "uuid" else "font-size:0.92rem;font-weight:600;"
    return (
        f'<div style="background:#1E293B;border-radius:8px;padding:12px 14px;'
        f'border-left:3px solid {colour};margin-bottom:6px;">'
        f'<div style="font-size:0.62rem;color:#94A3B8;text-transform:uppercase;'
        f'letter-spacing:.08em;margin-bottom:5px;">{label}</div>'
        f'<div style="color:#F1F5F9;{font}word-break:break-all;">{icon} {display}</div>'
        f'</div>'
    )


# ── Object renderer ─────────────────────────────────────────────────────────────

def _render_object(data: dict) -> None:
    """Render a flat object as a grid of styled field cards, handling nested dicts."""
    flat = pd.json_normalize(data, sep=" › ").to_dict(orient="records")
    if not flat:
        st.json(data)
        return

    pairs = list(flat[0].items())
    n_cols = min(len(pairs), 3)
    cols = st.columns(n_cols)
    for i, (raw_key, value) in enumerate(pairs):
        label   = raw_key.replace("_", " ").title()
        display, type_tag = _classify(raw_key.split(" › ")[-1], value)
        with cols[i % n_cols]:
            st.markdown(_field_card_html(label, display, type_tag), unsafe_allow_html=True)


# ── List / table renderer ───────────────────────────────────────────────────────

def _cell_to_str(value) -> str:
    """Convert a single dataframe cell value to a human-readable string.
    Handles dicts, lists, None, and primitives so nothing renders as [object Object].
    """
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "✅ Yes" if value else "❌ No"
    if isinstance(value, dict):
        # Flatten short dicts to "key: val, …"; show count for long ones
        pairs = [f"{k}: {v}" for k, v in value.items() if not isinstance(v, (dict, list))]
        if pairs:
            summary = ", ".join(pairs[:4])
            return summary + ("…" if len(pairs) > 4 else "")
        return f"{{{len(value)} fields}}"
    if isinstance(value, list):
        if not value:
            return "[ ]"
        # If list of simple scalars, join them
        if all(isinstance(i, (str, int, float, bool)) for i in value):
            joined = ", ".join(str(i) for i in value[:6])
            return joined + ("…" if len(value) > 6 else "")
        # List of objects — show count and key fields from first item
        if isinstance(value[0], dict):
            sample_keys = list(value[0].keys())[:3]
            return f"{len(value)} items  [{', '.join(sample_keys)}…]"
        return f"{len(value)} items"
    return value  # already a scalar


def _sanitise_df(df: pd.DataFrame) -> pd.DataFrame:
    """Final pass: convert any remaining dict/list cells to readable strings.
    Must run after all other formatting so nothing slips through as [object Object].
    """
    for col in df.columns:
        if df[col].apply(lambda v: isinstance(v, (dict, list))).any():
            df[col] = df[col].apply(_cell_to_str)
    return df


def _fmt_df_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Apply type-aware formatting to every column of a dataframe for display."""
    df = df.copy()
    for col in df.columns:
        col_key = col.split(".")[-1]  # handle dot-notated nested keys
        sample_non_null = df[col].dropna()
        if sample_non_null.empty:
            continue

        first = sample_non_null.iloc[0]
        # Skip columns that are already dicts/lists — _sanitise_df handles those
        if isinstance(first, (dict, list)):
            continue

        _, tag = _classify(col_key, first)

        if tag == "date":
            df[col] = df[col].apply(
                lambda v: _fmt_ts(v) or str(v) if v is not None else "—"
            )
        elif tag in ("bool_true", "bool_false"):
            df[col] = df[col].apply(
                lambda v: ("✅ Yes" if v else "❌ No") if isinstance(v, bool) else str(v)
            )
        elif tag == "cost":
            df[col] = df[col].apply(
                lambda v: f"${v:,.2f}" if isinstance(v, (int, float)) else str(v)
            )
        elif tag == "number":
            df[col] = df[col].apply(
                lambda v: f"{int(v):,}" if isinstance(v, int) else (f"{v:,.4f}" if isinstance(v, float) else str(v))
            )
        elif tag == "percent":
            df[col] = df[col].apply(
                lambda v: f"{v * 100:.1f}%" if isinstance(v, (int, float)) else str(v)
            )
    # Always sanitise remaining object cells last
    return _sanitise_df(df)


def _render_list(data: list, search_key: str = "_list_search") -> None:
    """Render a list as a formatted, searchable dataframe."""
    if not data:
        st.info("Empty list returned.")
        return

    df_raw  = pd.json_normalize(data)
    df_disp = _fmt_df_columns(df_raw)
    total   = len(df_disp)

    search = st.text_input(
        "Filter rows",
        placeholder="Search across all columns…",
        key=search_key,
    )
    if search:
        mask = df_disp.apply(
            lambda col: col.astype(str).str.contains(search, case=False, na=False)
        ).any(axis=1)
        df_disp = df_disp[mask]

    st.caption(f"Showing **{len(df_disp)}** of **{total}** rows")
    st.dataframe(df_disp, use_container_width=True, hide_index=True)


# ── Usage dashboard ─────────────────────────────────────────────────────────────

def _metric_tile(label: str, value, suffix: str = "", delta=None) -> None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        fmt = f"{int(value):,}{suffix}" if isinstance(value, int) else f"{value:,.2f}{suffix}"
    else:
        fmt = f"{value}{suffix}"
    st.metric(label=label, value=fmt, delta=delta)


def _build_id_lookup() -> dict[str, str]:
    """Build a UUID → display-name map from already-cached session state.
    No extra API calls — uses org, teams, and users that were fetched earlier.
    """
    lookup: dict[str, str] = {}
    org_id   = st.session_state.get("org_id", "")
    org_name = st.session_state.get("org_name", "")
    if org_id and org_name:
        lookup[org_id] = org_name

    # Teams cache key format matches _fetch_teams
    for key, val in st.session_state.items():
        if key.startswith("_teams_") and isinstance(val, list):
            for t in val:
                tid  = t.get("id", "")
                name = t.get("name", "")
                if tid and name:
                    lookup[tid] = name
        if key.startswith("_users_") and isinstance(val, list):
            for u in val:
                uid   = u.get("id", "")
                email = u.get("email", "")
                if uid and email:
                    lookup[uid] = email
    return lookup


_UUID_PATTERN = _re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", _re.I
)


def _resolve_model_label(model: str) -> str:
    """Return a human-readable label for a model string.
    Named models (e.g. 'claude-sonnet-4-20250514') are returned as-is.
    UUID models are shortened to 'uuid:abc12345…' for chart legibility.
    """
    if _UUID_PATTERN.match(model or ""):
        return f"uuid:{model[:8]}…"
    return model or "unknown"


def _render_usage_dashboard(data: dict, endpoint: dict) -> None:
    """Render usage response as BI metric tiles + charts."""
    usage_block = data.get("usage", data)
    items = usage_block.get("data", [])
    if not items:
        st.warning("No usage data returned for the selected date range.")
        return

    id_lookup = _build_id_lookup()

    def _resolve(uid: str) -> str:
        """Return display name for a UUID, or the raw value if not found."""
        return id_lookup.get(uid, uid) if uid else "—"

    def _sum(key, nested=None):
        total = 0
        for item in items:
            src = item.get(nested, item) if nested else item
            total += src.get(key, 0) if isinstance(src, dict) else 0
        return total

    is_v2 = "v2" in endpoint.get("path", "")

    # ── Context banner ─────────────────────────────────────────────────────
    ctx_fields: list[tuple[str, str]] = []
    org_id  = data.get("organizationId", "")
    user_id = data.get("userId", "")
    team_id = data.get("teamId", "")
    date_from = data.get("from", "")
    date_to   = data.get("to", "")

    if org_id:
        resolved = _resolve(org_id)
        ctx_fields.append(("Organisation", resolved if resolved != org_id else org_id[:8] + "…"))
    if user_id:
        resolved = _resolve(user_id)
        ctx_fields.append(("User", resolved if resolved != user_id else user_id[:8] + "…"))
    if team_id:
        resolved = _resolve(team_id)
        ctx_fields.append(("Team", resolved if resolved != team_id else team_id[:8] + "…"))
    if date_from or date_to:
        def _fmt_d(iso: str) -> str:
            try:
                return datetime.strptime(iso[:10], "%Y-%m-%d").strftime("%-d %b %Y")
            except Exception:
                try:
                    return datetime.strptime(iso[:10], "%Y-%m-%d").strftime("%d %b %Y")
                except Exception:
                    return iso[:10]
        ctx_fields.append(("Period", f"{_fmt_d(date_from)}  →  {_fmt_d(date_to)}"))

    if ctx_fields:
        ctx_cols = st.columns(len(ctx_fields))
        for i, (label, value) in enumerate(ctx_fields):
            with ctx_cols[i]:
                st.markdown(
                    f'<div style="background:#1E3A5F;border-radius:8px;padding:8px 14px;margin-bottom:12px;">'
                    f'<div style="font-size:0.65rem;color:#93C5FD;text-transform:uppercase;'
                    f'letter-spacing:.08em;">{label}</div>'
                    f'<div style="font-size:0.95rem;font-weight:700;color:#F8FAFC;'
                    f'white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{value}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

    # ── KPI tiles ─────────────────────────────────────────────────────────
    st.subheader("Summary")
    if is_v2:
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1: _metric_tile("Active Users",      _sum("activeUsers"))
        with c2: _metric_tile("Tokens Consumed",   _sum("totalTokensConsumed"))
        with c3: _metric_tile("Input Tokens",      _sum("totalInputTokens"))
        with c4: _metric_tile("Output Tokens",     _sum("totalOutputTokens"))
        with c5: _metric_tile("Total Cost",        _sum("totalCost"), suffix=" $")
    else:
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        with c1: _metric_tile("Active Users",       _sum("activeUsers"))
        with c2: _metric_tile("Completions",        _sum("completions",     "codeCompletions"))
        with c3: _metric_tile("Chars Completed",    _sum("charsCompleted",  "codeCompletions"))
        with c4: _metric_tile("Chat Interactions",  _sum("interactions",    "chat"))
        with c5: _metric_tile("Agent Interactions", _sum("interactions",    "agent"))
        with c6: _metric_tile("Automation Factor",
                              round(_sum("automationFactor", "codeCompletions") / max(len(items), 1), 2))

    # ── Trend chart ────────────────────────────────────────────────────────
    if len(items) > 1:
        st.subheader("Trend")
        df_trend = pd.DataFrame(items)
        df_trend["from"] = pd.to_datetime(df_trend["from"], errors="coerce")

        if is_v2 and "totalTokensConsumed" in df_trend.columns:
            fig = px.line(
                df_trend, x="from",
                y=["totalTokensConsumed", "totalInputTokens", "totalOutputTokens"],
                labels={"value": "Tokens", "from": "Date", "variable": "Metric"},
                title="Token Consumption Over Time",
            )
        elif "activeUsers" in df_trend.columns:
            fig = px.bar(
                df_trend, x="from", y="activeUsers",
                labels={"activeUsers": "Active Users", "from": "Date"},
                title="Active Users Over Time",
            )
        else:
            fig = None

        if fig:
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#F8FAFC", legend_title_text="",
            )
            st.plotly_chart(fig, use_container_width=True)

    # ── Model breakdown donut (v2 only) ────────────────────────────────────
    if is_v2:
        model_rows = [mb for item in items for mb in item.get("modelBreakdown", [])]
        if model_rows:
            st.subheader("Model Breakdown")
            df_m = pd.DataFrame(model_rows)
            if "model" in df_m.columns and "tokensConsumed" in df_m.columns:
                df_m["model"] = df_m["model"].apply(_resolve_model_label)
                agg = df_m.groupby("model", as_index=False)["tokensConsumed"].sum()
                fig2 = px.pie(agg, names="model", values="tokensConsumed",
                              title="Tokens by Model", hole=0.4)
                fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#F8FAFC")
                st.plotly_chart(fig2, use_container_width=True)

    # ── Data table ─────────────────────────────────────────────────────────
    st.subheader("Data Table")
    # Fully flatten nested objects (codeCompletions, chat, agent, models…)
    # sep=" › " gives readable column names like "chat › models › inputTokens"
    df_flat = pd.json_normalize(items, sep=" › ")
    # Resolve known UUID columns to display names
    _id_cols = {"organizationId", "userId", "teamId", "organizationid", "userid", "teamid"}
    for col in df_flat.columns:
        if col in _id_cols or col.split(" › ")[-1] in _id_cols:
            df_flat[col] = df_flat[col].apply(
                lambda v: f"{id_lookup[v]}  ({v[:8]}…)" if v in id_lookup else v
            )
    # Any list/dict cells that survived (e.g. models arrays) get converted to strings
    df_flat = _fmt_df_columns(df_flat)
    # Rename columns for readability — strip leading path segments when unambiguous
    short_names = {}
    for col in df_flat.columns:
        parts = col.split(" › ")
        short = parts[-1] if parts[-1] not in short_names.values() else col
        short_names[col] = short
    df_flat = df_flat.rename(columns=short_names)
    st.dataframe(df_flat, use_container_width=True, hide_index=True)


# ── Top-level response router ───────────────────────────────────────────────────

def render_response(code: int, data: dict | list, endpoint: dict | None = None) -> None:
    """Route API response to the best renderer and always offer a Raw JSON tab."""
    st.markdown(f"**Status:** {status_badge(code)}")

    if code == 0 or not (200 <= code < 300):
        st.json(data)
        return

    ep   = endpoint or {}
    path = ep.get("path", "")

    # ── Usage endpoints → BI dashboard ────────────────────────────────────
    if "usage" in path and isinstance(data, dict):
        tab_dash, tab_raw = st.tabs(["📊 Dashboard", "{ } Raw JSON"])
        with tab_dash:
            _render_usage_dashboard(data, ep)
        with tab_raw:
            st.json(data)
        return

    # ── Top-level array ────────────────────────────────────────────────────
    if isinstance(data, list):
        tab_table, tab_raw = st.tabs(["📋 Table", "{ } Raw JSON"])
        with tab_table:
            _render_list(data)
        with tab_raw:
            st.json(data)
        return

    # ── Dict with a nested list under a known key ──────────────────────────
    if isinstance(data, dict):
        list_key = next(
            (k for k in ("data", "items", "users", "teams", "results", "permissions")
             if k in data and isinstance(data[k], list)),
            None,
        )
        if list_key:
            tab_table, tab_raw = st.tabs(["📋 Table", "{ } Raw JSON"])
            with tab_table:
                # Show pagination / meta fields above the table
                meta = {k: v for k, v in data.items() if k != list_key and not isinstance(v, (dict, list))}
                if meta:
                    mcols = st.columns(min(len(meta), 5))
                    for i, (k, v) in enumerate(meta.items()):
                        display, tag = _classify(k, v)
                        with mcols[i % len(mcols)]:
                            st.markdown(_field_card_html(k.replace("_", " ").title(), display, tag),
                                        unsafe_allow_html=True)
                _render_list(data[list_key], search_key="_nested_list_search")
            with tab_raw:
                st.json(data)
            return

    # ── Single object (org, license, etc.) ────────────────────────────────
    tab_overview, tab_raw = st.tabs(["🗂 Overview", "{ } Raw JSON"])
    with tab_overview:
        _render_object(data)
    with tab_raw:
        st.json(data)


# ── Sidebar ────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.image(
        "https://www.tabnine.com/wp-content/uploads/2023/12/Tabnine_Logo_Horizontal.png",
        use_container_width=True,
    )
    st.markdown("---")
    st.subheader("🔑 Authentication")

    with st.expander("⚙️ Advanced — API base URL"):
        base_url_override = st.text_input(
            "Base URL",
            value=BASE_URL,
            help="Override if the Tabnine docs show a different host or path prefix.",
        )
        if base_url_override != BASE_URL:
            st.warning("Using custom base URL.")
    BASE_URL_EFFECTIVE = base_url_override

    token = st.text_input(
        "API Token",
        type="password",
        placeholder="Paste your Tabnine API token here",
        help="Your token is never stored. It lives only in this browser session.",
    )

    if token:
        # Auto-fetch org details whenever the token changes
        if st.session_state.get("_token_hash") != hash(token + BASE_URL_EFFECTIVE):
            with st.spinner("Verifying token…"):
                _code, _org = make_request(
                    token, "GET", "/api/v1/organization", base_url=BASE_URL_EFFECTIVE
                )
            if _code == 200 and isinstance(_org, dict):
                st.session_state["org_id"]   = _org.get("id", "")
                st.session_state["org_name"] = _org.get("name", "Unknown org")
                st.session_state["org_data"] = _org
                st.session_state["token_ok"] = True
            else:
                st.session_state["org_id"]   = ""
                st.session_state["org_name"] = ""
                st.session_state["org_data"] = {}
                st.session_state["token_ok"] = False
            st.session_state["_token_hash"] = hash(token + BASE_URL_EFFECTIVE)

        if st.session_state.get("token_ok"):
            st.success("Token valid ✓")
            org_name = st.session_state.get("org_name", "")
            org_id   = st.session_state.get("org_id", "")
            st.markdown(
                f"""<div style="background:#1E293B;border-radius:8px;padding:10px 14px;margin-top:6px;">
                <div style="font-size:0.7rem;color:#94A3B8;text-transform:uppercase;letter-spacing:.05em;">Organisation</div>
                <div style="font-size:1rem;font-weight:700;color:#F8FAFC;">{org_name}</div>
                <div style="font-size:0.7rem;color:#64748B;margin-top:2px;word-break:break-all;">{org_id}</div>
                </div>""",
                unsafe_allow_html=True,
            )
        else:
            st.error("Token invalid or org unreachable.")
    else:
        st.warning("Enter a token to get started.")

    st.markdown("---")
    st.subheader("📚 Resources")
    st.markdown(f"[Official API Docs]({DOCS_BASE})")
    st.markdown("[Tabnine Admin Console](https://app.tabnine.com)")
    st.markdown("[Tabnine Homepage](https://www.tabnine.com)")

    st.markdown("---")
    st.caption(f"Demo built with [Streamlit](https://streamlit.io) · {datetime.now().year}")


# ── Main area ──────────────────────────────────────────────────────────────────

st.title("Tabnine API Demo")
st.markdown(
    "This tool lets you interactively explore every endpoint of the "
    "[Tabnine Team Management API](%s). Select a capability below, "
    "fill in any required parameters, and run the call live." % DOCS_BASE
)
st.markdown("---")

if not token:
    st.info("👈 Enter your API token in the sidebar to get started.")
    st.stop()

# ── Endpoint selector ──────────────────────────────────────────────────────────

# Build grouped display labels: "v1 · Users › List Users"
def _group_label(name: str, ep: dict) -> str:
    return f"{ep['version']} · {ep['category']}  ›  {name.split(' · ', 1)[-1]}"

endpoint_labels = {name: _group_label(name, ep) for name, ep in API_ENDPOINTS.items()}
label_to_name = {v: k for k, v in endpoint_labels.items()}

selected_label = st.selectbox(
    "Select an API capability to demo",
    options=list(endpoint_labels.values()),
    index=0,
)
selected_name = label_to_name[selected_label]
endpoint = API_ENDPOINTS[selected_name]

# ── Endpoint header ────────────────────────────────────────────────────────────

version_colour = "#7C3AED" if endpoint["version"] == "v2" else "#0369A1"
version_badge = (
    f'<span style="background:{version_colour};color:white;padding:2px 8px;'
    f'border-radius:4px;font-size:0.75rem;font-weight:700;margin-right:8px;">'
    f'{endpoint["version"].upper()}</span>'
)
method_colours = {"GET": "#16A34A", "POST": "#D97706", "DELETE": "#DC2626", "PATCH": "#7C3AED", "PUT": "#0369A1"}
method_colour = method_colours.get(endpoint["method"], "#6B7280")
method_badge = (
    f'<span style="background:{method_colour};color:white;padding:2px 8px;'
    f'border-radius:4px;font-size:0.75rem;font-weight:700;margin-right:8px;">'
    f'{endpoint["method"]}</span>'
)

col_info, col_doc = st.columns([3, 1])

with col_info:
    st.markdown(
        f'{version_badge}{method_badge}'
        f'<code style="font-size:0.9rem;">{BASE_URL_EFFECTIVE}{endpoint["path"]}</code>',
        unsafe_allow_html=True,
    )
    st.markdown(f"**{selected_name.split(' · ', 1)[-1]}** — {endpoint['description']}")

with col_doc:
    doc_url = f"{DOCS_BASE}{endpoint['doc_anchor']}"
    st.markdown(f"#### 📄 Docs\n[View in official docs →]({doc_url})")

st.markdown("---")

# ── Path parameter inputs ──────────────────────────────────────────────────────

path_values: dict[str, str] = {}

if endpoint["path_params"]:
    st.subheader("Path Parameters")
    pp_cols = st.columns(min(len(endpoint["path_params"]), 3))
    for i, key in enumerate(endpoint["path_params"]):
        with pp_cols[i % len(pp_cols)]:
            path_values[key] = _smart_param_input(
                key=key,
                default="",
                hint=f"Required path segment: {key}",
                widget_key=f"path_{selected_name}_{key}",
                token=token,
                base_url=BASE_URL_EFFECTIVE,
                required=True,
            )

# ── Query parameter inputs ─────────────────────────────────────────────────────

query_values: dict[str, str] = {}

if endpoint["query_params"]:
    st.subheader("Query Parameters")
    # Use 2 columns so date pickers and dropdowns have breathing room
    n_qp_cols = min(len(endpoint["query_params"]), 2)
    qp_cols = st.columns(n_qp_cols)
    for i, (key, default, hint) in enumerate(endpoint["query_params"]):
        # Auto-fill organizationId before passing to the smart dispatcher
        if key == "organizationId" and not default:
            default = st.session_state.get("org_id", "")
        with qp_cols[i % n_qp_cols]:
            query_values[key] = _smart_param_input(
                key=key,
                default=default,
                hint=hint,
                widget_key=f"query_{selected_name}_{key}",
                token=token,
                base_url=BASE_URL_EFFECTIVE,
            )

# ── Body field inputs ──────────────────────────────────────────────────────────

body: dict | None = None

if endpoint["body_fields"]:
    st.subheader("Request Body")
    bf_cols = st.columns(min(len(endpoint["body_fields"]), 2))
    body_values: dict[str, str] = {}
    for i, (key, default, hint) in enumerate(endpoint["body_fields"]):
        with bf_cols[i % len(bf_cols)]:
            body_values[key] = _smart_param_input(
                key=key,
                default=default,
                hint=hint,
                widget_key=f"body_{selected_name}_{key}",
                token=token,
                base_url=BASE_URL_EFFECTIVE,
            )
    # Parse JSON array fields transparently
    parsed_body: dict = {}
    for k, v in body_values.items():
        if v.strip().startswith("["):
            try:
                parsed_body[k] = json.loads(v)
            except json.JSONDecodeError:
                parsed_body[k] = v
        elif v.lower() in ("true", "false"):
            parsed_body[k] = v.lower() == "true"
        elif v:
            parsed_body[k] = v
    if parsed_body:
        body = parsed_body

# ── Destructive action warning ─────────────────────────────────────────────────

is_destructive = endpoint["method"] == "DELETE" or any(w in selected_name for w in ("Remove", "Revoke", "Delete"))
confirmed = True

if is_destructive:
    st.warning(
        "⚠️ This is a **destructive action** and will modify your live team data. "
        "Check the box below to confirm before running."
    )
    confirmed = st.checkbox("Yes, I understand — proceed with this action.")

# ── Run button ─────────────────────────────────────────────────────────────────

run_disabled = not confirmed

if st.button(
    f"▶  Run  —  {endpoint['method']}  {endpoint['path']}",
    disabled=run_disabled,
    type="primary",
):
    # Resolve path placeholders
    resolved_path = build_path(endpoint["path"], path_values)

    # Build query dict (non-empty values only) — requests handles URL encoding
    query_dict = {k: v for k, v in query_values.items() if v}

    # Build display URL (approximate — requests will properly encode special chars)
    qs_display = "&".join(f"{k}={v}" for k, v in query_dict.items())
    full_url = f"{BASE_URL_EFFECTIVE}{resolved_path}" + (f"?{qs_display}" if qs_display else "")

    with st.spinner("Calling the Tabnine API..."):
        status_code, response_data = make_request(
            token=token,
            method=endpoint["method"],
            path=resolved_path,
            body=body,
            base_url=BASE_URL_EFFECTIVE,
            query_params=query_dict if query_dict else None,
        )

    st.markdown("---")
    st.subheader("Response")
    st.caption(f"Request sent to: `{full_url}`")
    render_response(status_code, response_data, endpoint=endpoint)

    # ── cURL equivalent ────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("Equivalent cURL command")
    curl_body = f" \\\n  -d '{json.dumps(body, indent=2)}'" if body else ""
    curl_cmd = (
        f"curl -X {endpoint['method']} \\\n"
        f"  '{full_url}' \\\n"
        f"  -H 'Authorization: Bearer <YOUR_TOKEN>' \\\n"
        f"  -H 'Content-Type: application/json'"
        f"{curl_body}"
    )
    st.code(curl_cmd, language="bash")
    st.caption(f"[Full documentation for this endpoint]({DOCS_BASE}{endpoint['doc_anchor']})")

# ── API Overview table (always visible at the bottom) ─────────────────────────

st.markdown("---")
with st.expander("📋 All available API capabilities", expanded=False):
    rows = []
    for name, ep in API_ENDPOINTS.items():
        rows.append({
            "Version": ep["version"].upper(),
            "Category": ep["category"],
            "Capability": name.split(" · ", 1)[-1],
            "Method": ep["method"],
            "Path": ep["path"],
            "Description": ep["description"],
            "Docs": f"{DOCS_BASE}{ep['doc_anchor']}",
        })
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
