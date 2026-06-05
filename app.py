import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime

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

    "v1 · List Users": {
        "method": "GET",
        "path": "/api/v1/users",
        "version": "v1",
        "category": "Users",
        "description": "Retrieve a paginated list of all users in your Tabnine organisation.",
        "doc_anchor": "#list-users",
        "path_params": [],
        "body_fields": [],
        "query_params": [],
    },
    "v1 · Get User": {
        "method": "GET",
        "path": "/api/v1/users/{email}",
        "version": "v1",
        "category": "Users",
        "description": "Retrieve details for a specific user by their email address. Returns id, username, email, role, verified, active, team, and allowedTeams.",
        "doc_anchor": "#get-user",
        "path_params": ["email"],
        "body_fields": [],
        "query_params": [],
    },
    "v1 · Add User": {
        "method": "POST",
        "path": "/api/v1/users",
        "version": "v1",
        "category": "Users",
        "description": "Add a new user to your Tabnine organisation and assign a seat. Specify role (Member/Admin), whether they are active, and optionally a teamId.",
        "doc_anchor": "#add-user",
        "path_params": [],
        "body_fields": [
            ("email", "newuser@example.com", "User's email address"),
            ("role", "Member", "Member or Admin"),
            ("active", "true", "true or false"),
            ("teamId", "", "UUID of the team to assign (optional)"),
        ],
        "query_params": [],
    },
    "v1 · Update User": {
        "method": "POST",
        "path": "/api/v1/users/{email}",
        "version": "v1",
        "category": "Users",
        "description": "Update an existing user's role, active status, or team assignment.",
        "doc_anchor": "#update-user",
        "path_params": ["email"],
        "body_fields": [
            ("role", "Member", "Member or Admin"),
            ("active", "true", "true or false"),
            ("teamId", "", "UUID of the team to assign (optional)"),
        ],
        "query_params": [],
    },
    "v1 · Remove User": {
        "method": "DELETE",
        "path": "/api/v1/users/{email}",
        "version": "v1",
        "category": "Users",
        "description": "Remove a user from your Tabnine organisation and release their seat.",
        "doc_anchor": "#remove-user",
        "path_params": ["email"],
        "body_fields": [],
        "query_params": [],
    },

    # ── v1 · Groups ───────────────────────────────────────────────────────────

    "v1 · List Groups": {
        "method": "GET",
        "path": "/api/v1/groups",
        "version": "v1",
        "category": "Groups",
        "description": "Retrieve all groups defined in your Tabnine organisation.",
        "doc_anchor": "#list-groups",
        "path_params": [],
        "body_fields": [],
        "query_params": [],
    },
    "v1 · Get Group": {
        "method": "GET",
        "path": "/api/v1/groups/{group_name}",
        "version": "v1",
        "category": "Groups",
        "description": "Retrieve details for a specific group by name.",
        "doc_anchor": "#get-group",
        "path_params": ["group_name"],
        "body_fields": [],
        "query_params": [],
    },
    "v1 · Create Group": {
        "method": "POST",
        "path": "/api/v1/groups",
        "version": "v1",
        "category": "Groups",
        "description": "Create a new group in your Tabnine organisation.",
        "doc_anchor": "#create-group",
        "path_params": [],
        "body_fields": [
            ("group_name", "my-new-group", "Name of the group to create"),
        ],
        "query_params": [],
    },
    "v1 · Delete Group": {
        "method": "DELETE",
        "path": "/api/v1/groups/{group_name}",
        "version": "v1",
        "category": "Groups",
        "description": "Delete an existing group from your Tabnine organisation.",
        "doc_anchor": "#delete-group",
        "path_params": ["group_name"],
        "body_fields": [],
        "query_params": [],
    },
    "v1 · Add User to Group": {
        "method": "POST",
        "path": "/api/v1/groups/{group_name}/users",
        "version": "v1",
        "category": "Groups",
        "description": "Add an existing user to a specific group.",
        "doc_anchor": "#add-user-to-group",
        "path_params": ["group_name"],
        "body_fields": [
            ("email", "user@example.com", "Email of the user to add"),
        ],
        "query_params": [],
    },
    "v1 · Remove User from Group": {
        "method": "DELETE",
        "path": "/api/v1/groups/{group_name}/users/{email}",
        "version": "v1",
        "category": "Groups",
        "description": "Remove a user from a specific group.",
        "doc_anchor": "#remove-user-from-group",
        "path_params": ["group_name", "email"],
        "body_fields": [],
        "query_params": [],
    },

    # ── v2 · Teams ────────────────────────────────────────────────────────────

    "v2 · List Teams": {
        "method": "GET",
        "path": "/api/v2/teams",
        "version": "v2",
        "category": "Teams",
        "description": "Retrieve all teams in your organisation. Each team includes id, name, organizationId, syncedGroupId, usersCount, and isDefaultTeam.",
        "doc_anchor": "#list-teams",
        "path_params": [],
        "body_fields": [],
        "query_params": [],
    },
    "v2 · Create Team": {
        "method": "POST",
        "path": "/api/v2/teams",
        "version": "v2",
        "category": "Teams",
        "description": "Create a new team. Returns the created team object including its generated UUID.",
        "doc_anchor": "#create-team",
        "path_params": [],
        "body_fields": [
            ("name", "my-team", "Display name for the new team"),
        ],
        "query_params": [],
    },
    "v2 · Get Teams for User": {
        "method": "GET",
        "path": "/api/v2/users/{email}/teams",
        "version": "v2",
        "category": "Teams",
        "description": "Retrieve the teams a specific user belongs to, including their role and the team's default status.",
        "doc_anchor": "#get-teams-for-user",
        "path_params": ["email"],
        "body_fields": [],
        "query_params": [],
    },
    "v2 · Set Teams for User": {
        "method": "POST",
        "path": "/api/v2/users/{email}/teams",
        "version": "v2",
        "category": "Teams",
        "description": "Replace the full set of teams a user belongs to by providing an array of teamIds.",
        "doc_anchor": "#set-teams-for-user",
        "path_params": ["email"],
        "body_fields": [
            ("teamIds", '["123e4567-e89b-12d3-a456-426614174000"]', "JSON array of team UUIDs"),
        ],
        "query_params": [],
    },
    "v2 · Add User to Team": {
        "method": "POST",
        "path": "/api/v2/teams/{teamId}/users",
        "version": "v2",
        "category": "Teams",
        "description": "Add a user to a team. Specify the user's email, teamId, and role.",
        "doc_anchor": "#add-user-to-team",
        "path_params": ["teamId"],
        "body_fields": [
            ("email", "user@example.com", "Email of the user to add"),
            ("teamId", "123e4567-e89b-12d3-a456-426614174000", "Team UUID (must match path)"),
            ("role", "Member", "Member or Admin"),
        ],
        "query_params": [],
    },
    "v2 · Remove User from Team": {
        "method": "DELETE",
        "path": "/api/v2/teams/{teamId}/users/{email}",
        "version": "v2",
        "category": "Teams",
        "description": "Remove a user from a specific team.",
        "doc_anchor": "#remove-user-from-team",
        "path_params": ["teamId", "email"],
        "body_fields": [],
        "query_params": [],
    },

    # ── v2 · Invitations ──────────────────────────────────────────────────────

    "v2 · List Invitations": {
        "method": "GET",
        "path": "/api/v2/invitations",
        "version": "v2",
        "category": "Invitations",
        "description": "List pending invitations for your organisation. Returns id, email, teamId, role, createdAt, expiresAt, and revokedAt for each invitation.",
        "doc_anchor": "#list-invitations",
        "path_params": [],
        "body_fields": [],
        "query_params": [],
    },
    "v2 · Create Invitation": {
        "method": "POST",
        "path": "/api/v2/invitations",
        "version": "v2",
        "category": "Invitations",
        "description": "Invite a user to join a team. Returns success, message, userExists, and userId.",
        "doc_anchor": "#create-invitation",
        "path_params": [],
        "body_fields": [
            ("email", "invitee@example.com", "Email address to invite"),
            ("teamId", "123e4567-e89b-12d3-a456-426614174000", "Team UUID to invite into"),
            ("role", "Member", "Member or Admin"),
        ],
        "query_params": [],
    },
    "v2 · Revoke Invitations": {
        "method": "POST",
        "path": "/api/v2/invitations/revoke",
        "version": "v2",
        "category": "Invitations",
        "description": "Revoke one or more pending invitations by their UUIDs. Returns the count of revoked invitations.",
        "doc_anchor": "#revoke-invitations",
        "path_params": [],
        "body_fields": [
            ("invitationIds", '["123e4567-e89b-12d3-a456-426614174000"]', "JSON array of invitation UUIDs"),
        ],
        "query_params": [],
    },

    # ── v2 · Usage ────────────────────────────────────────────────────────────

    "v2 · Org Usage": {
        "method": "GET",
        "path": "/api/v2/usage/org",
        "version": "v2",
        "category": "Usage",
        "description": "Retrieve organisation-wide usage statistics including activeUsers, totalTokensConsumed, totalInputTokens, totalOutputTokens, totalCost, and a modelBreakdown array.",
        "doc_anchor": "#org-usage",
        "path_params": [],
        "body_fields": [],
        "query_params": [
            ("from", "2026-01-01T00:00:00Z", "ISO 8601 start date"),
            ("to", "2026-03-31T00:00:00Z", "ISO 8601 end date"),
            ("granularity", "all", "all | daily | weekly | monthly"),
        ],
    },
    "v2 · Team Usage": {
        "method": "GET",
        "path": "/api/v2/usage/teams/{teamId}",
        "version": "v2",
        "category": "Usage",
        "description": "Retrieve usage statistics for a specific team, with the same shape as org usage but scoped to teamId.",
        "doc_anchor": "#team-usage",
        "path_params": ["teamId"],
        "body_fields": [],
        "query_params": [
            ("from", "2026-01-01T00:00:00Z", "ISO 8601 start date"),
            ("to", "2026-03-31T00:00:00Z", "ISO 8601 end date"),
            ("granularity", "all", "all | daily | weekly | monthly"),
        ],
    },
    "v2 · User Usage": {
        "method": "GET",
        "path": "/api/v2/usage/users/{userId}",
        "version": "v2",
        "category": "Usage",
        "description": "Retrieve usage statistics for a specific user, including code completions, chat, and agent metrics broken down by model.",
        "doc_anchor": "#user-usage",
        "path_params": ["userId"],
        "body_fields": [],
        "query_params": [
            ("from", "2026-01-01T00:00:00Z", "ISO 8601 start date"),
            ("to", "2026-03-31T00:00:00Z", "ISO 8601 end date"),
            ("granularity", "all", "all | daily | weekly | monthly"),
        ],
    },

    # ── v2 · Audit Log ────────────────────────────────────────────────────────

    "v2 · Audit Log": {
        "method": "GET",
        "path": "/api/v2/audit-log",
        "version": "v2",
        "category": "Audit Log",
        "description": "Retrieve a paginated audit log of admin actions. Each entry includes id, timestamp, eventType, actor (id/type/email/displayName), resource (id/type/name), metadata, and request details (ipAddress, userAgent, clientId, requestId).",
        "doc_anchor": "#audit-log",
        "path_params": [],
        "body_fields": [],
        "query_params": [
            ("limit", "50", "Max results per page"),
            ("offset", "0", "Pagination offset"),
        ],
    },

    # ── v2 · Context Repositories ─────────────────────────────────────────────

    "v2 · List Context Repos": {
        "method": "GET",
        "path": "/api/v2/context/repositories",
        "version": "v2",
        "category": "Context Repositories",
        "description": "List all context repositories configured for your organisation. Each entry includes repository_link, repo_type, authentication_method, authentication_credentials_name, and view_source_link_pattern.",
        "doc_anchor": "#list-context-repos",
        "path_params": [],
        "body_fields": [],
        "query_params": [],
    },
    "v2 · Add Context Repo": {
        "method": "POST",
        "path": "/api/v2/context/repositories",
        "version": "v2",
        "category": "Context Repositories",
        "description": "Add a new context repository for Tabnine to index. Specify the repository link, type, authentication method, credential name, and an optional view-source link pattern.",
        "doc_anchor": "#add-context-repo",
        "path_params": [],
        "body_fields": [
            ("repository_link", "https://github.com/org/repo", "Full URL of the repository"),
            ("repo_type", "git", "git"),
            ("authentication_method", "ssh", "ssh or token"),
            ("authentication_credentials_name", "my-cred", "Name of the stored credential"),
            ("view_source_link_pattern", "", "Optional URL pattern for source links"),
        ],
        "query_params": [],
    },
    "v2 · Update Context Repo": {
        "method": "POST",
        "path": "/api/v2/context/repositories/{repository_link}",
        "version": "v2",
        "category": "Context Repositories",
        "description": "Update an existing context repository's authentication method, credential name, or view-source link pattern.",
        "doc_anchor": "#update-context-repo",
        "path_params": ["repository_link"],
        "body_fields": [
            ("repo_type", "git", "git"),
            ("authentication_method", "ssh", "ssh or token"),
            ("authentication_credentials_name", "my-cred", "Name of the stored credential"),
            ("view_source_link_pattern", "", "Optional URL pattern for source links"),
        ],
        "query_params": [],
    },
    "v2 · Delete Context Repo": {
        "method": "DELETE",
        "path": "/api/v2/context/repositories/{repository_link}",
        "version": "v2",
        "category": "Context Repositories",
        "description": "Remove a context repository from your organisation's Tabnine configuration.",
        "doc_anchor": "#delete-context-repo",
        "path_params": ["repository_link"],
        "body_fields": [],
        "query_params": [],
    },
}

# ── Helpers ────────────────────────────────────────────────────────────────────

def make_request(token: str, method: str, path: str, body: dict | None = None, base_url: str = BASE_URL) -> tuple[int, dict]:
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


def render_response(code: int, data: dict):
    """Render the API response in a structured, readable way."""
    st.markdown(f"**Status:** {status_badge(code)}")

    if isinstance(data, list):
        if data and isinstance(data[0], dict):
            try:
                st.dataframe(pd.DataFrame(data), use_container_width=True)
                return
            except Exception:
                pass
    st.json(data)


# ── Sidebar ────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.image(
        "https://www.tabnine.com/wp-content/uploads/2023/12/Tabnine_Logo_Horizontal.png",
        use_container_width=True,
    )
    st.markdown("---")
    st.subheader("🔑 Authentication")
    token = st.text_input(
        "API Token",
        type="password",
        placeholder="Paste your Tabnine API token here",
        help="Your token is never stored. It lives only in this browser session.",
    )
    if token:
        st.success("Token loaded ✓")
    else:
        st.warning("Enter a token to enable API calls.")

    with st.expander("⚙️ Advanced — API base URL"):
        base_url_override = st.text_input(
            "Base URL",
            value=BASE_URL,
            help="Override if the Tabnine docs show a different host or path prefix.",
        )
        if base_url_override != BASE_URL:
            st.warning("Using custom base URL.")
    BASE_URL_EFFECTIVE = base_url_override

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
method_colours = {"GET": "#16A34A", "POST": "#D97706", "DELETE": "#DC2626"}
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
            path_values[key] = st.text_input(
                key.replace("_", " ").title(),
                value="",
                key=f"path_{selected_name}_{key}",
                placeholder=f"Required — {key}",
            )

# ── Query parameter inputs ─────────────────────────────────────────────────────

query_values: dict[str, str] = {}

if endpoint["query_params"]:
    st.subheader("Query Parameters")
    qp_cols = st.columns(min(len(endpoint["query_params"]), 3))
    for i, (key, default, hint) in enumerate(endpoint["query_params"]):
        with qp_cols[i % len(qp_cols)]:
            query_values[key] = st.text_input(
                key.replace("_", " ").title(),
                value=default,
                key=f"query_{selected_name}_{key}",
                help=hint,
            )

# ── Body field inputs ──────────────────────────────────────────────────────────

body: dict | None = None

if endpoint["body_fields"]:
    st.subheader("Request Body")
    bf_cols = st.columns(min(len(endpoint["body_fields"]), 3))
    body_values: dict[str, str] = {}
    for i, (key, default, hint) in enumerate(endpoint["body_fields"]):
        with bf_cols[i % len(bf_cols)]:
            body_values[key] = st.text_input(
                key.replace("_", " ").title(),
                value=default,
                key=f"body_{selected_name}_{key}",
                help=hint,
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

is_destructive = endpoint["method"] == "DELETE" or "Remove" in selected_name or "Revoke" in selected_name
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

    # Build query string
    qs = "&".join(f"{k}={v}" for k, v in query_values.items() if v)
    full_url = f"{BASE_URL_EFFECTIVE}{resolved_path}" + (f"?{qs}" if qs else "")

    with st.spinner("Calling the Tabnine API..."):
        status_code, response_data = make_request(
            token=token,
            method=endpoint["method"],
            path=resolved_path + (f"?{qs}" if qs else ""),
            body=body,
            base_url=BASE_URL_EFFECTIVE,
        )

    st.markdown("---")
    st.subheader("Response")
    st.caption(f"Request sent to: `{full_url}`")
    render_response(status_code, response_data)

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
