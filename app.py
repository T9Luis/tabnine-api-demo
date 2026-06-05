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
BASE_URL = "https://webapi.tabnine.com"

DOCS_BASE = "https://docs.tabnine.com/main/administering-tabnine/managing-your-team/tabnine-apis"

API_ENDPOINTS = {
    "List Users": {
        "method": "GET",
        "path": "/api/v1/users",
        "description": "Retrieve a list of all users in your Tabnine team.",
        "doc_anchor": "#list-users",
        "params": {},
    },
    "Get User": {
        "method": "GET",
        "path": "/api/v1/users/{email}",
        "description": "Retrieve details for a specific user by their email address.",
        "doc_anchor": "#get-user",
        "params": {"email": "user@example.com"},
    },
    "Add User": {
        "method": "POST",
        "path": "/api/v1/users",
        "description": "Add a new user to your Tabnine team and assign a seat.",
        "doc_anchor": "#add-user",
        "params": {"email": "newuser@example.com"},
    },
    "Remove User": {
        "method": "DELETE",
        "path": "/api/v1/users/{email}",
        "description": "Remove a user from your Tabnine team and release their seat.",
        "doc_anchor": "#remove-user",
        "params": {"email": "user@example.com"},
    },
    "List Groups": {
        "method": "GET",
        "path": "/api/v1/groups",
        "description": "Retrieve all groups (teams/departments) defined in your Tabnine organisation.",
        "doc_anchor": "#list-groups",
        "params": {},
    },
    "Get Group": {
        "method": "GET",
        "path": "/api/v1/groups/{group_name}",
        "description": "Retrieve details for a specific group by name.",
        "doc_anchor": "#get-group",
        "params": {"group_name": "engineering"},
    },
    "Create Group": {
        "method": "POST",
        "path": "/api/v1/groups",
        "description": "Create a new group in your Tabnine organisation.",
        "doc_anchor": "#create-group",
        "params": {"group_name": "my-new-group"},
    },
    "Delete Group": {
        "method": "DELETE",
        "path": "/api/v1/groups/{group_name}",
        "description": "Delete an existing group from your Tabnine organisation.",
        "doc_anchor": "#delete-group",
        "params": {"group_name": "my-new-group"},
    },
    "Add User to Group": {
        "method": "POST",
        "path": "/api/v1/groups/{group_name}/users",
        "description": "Add an existing user to a specific group.",
        "doc_anchor": "#add-user-to-group",
        "params": {"group_name": "engineering", "email": "user@example.com"},
    },
    "Remove User from Group": {
        "method": "DELETE",
        "path": "/api/v1/groups/{group_name}/users/{email}",
        "description": "Remove a user from a specific group.",
        "doc_anchor": "#remove-user-from-group",
        "params": {"group_name": "engineering", "email": "user@example.com"},
    },
    "Usage Report": {
        "method": "GET",
        "path": "/api/v1/usage",
        "description": "Retrieve usage statistics (completions accepted, suggested, etc.) for your team.",
        "doc_anchor": "#usage-report",
        "params": {},
    },
}

# ── Helpers ────────────────────────────────────────────────────────────────────

def make_request(token: str, method: str, path: str, body: dict | None = None) -> tuple[int, dict]:
    """Execute an authenticated request against the Tabnine API."""
    url = f"{BASE_URL}{path}"
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

selected_name = st.selectbox(
    "Select an API capability to demo",
    options=list(API_ENDPOINTS.keys()),
    index=0,
)

endpoint = API_ENDPOINTS[selected_name]

col_info, col_doc = st.columns([3, 1])

with col_info:
    st.subheader(selected_name)
    st.markdown(endpoint["description"])
    st.markdown(
        f"`{endpoint['method']}` &nbsp; `{BASE_URL}{endpoint['path']}`",
        unsafe_allow_html=True,
    )

with col_doc:
    doc_url = f"{DOCS_BASE}{endpoint['doc_anchor']}"
    st.markdown(f"#### 📄 Docs\n[View in official docs →]({doc_url})")

st.markdown("---")

# ── Parameter inputs ───────────────────────────────────────────────────────────

filled_params: dict = {}
body: dict | None = None
path_params = set()

# Detect which params are path-level vs body-level
for placeholder in ["email", "group_name"]:
    if f"{{{placeholder}}}" in endpoint["path"]:
        path_params.add(placeholder)

param_keys = list(endpoint["params"].keys())

if param_keys:
    st.subheader("Parameters")
    param_cols = st.columns(min(len(param_keys), 3))

    for i, key in enumerate(param_keys):
        with param_cols[i % len(param_cols)]:
            label = key.replace("_", " ").title()
            default = endpoint["params"][key]

            # Destructive actions get a confirmation checkbox instead of running freely
            if endpoint["method"] in ("DELETE", "POST") and key == "email":
                value = st.text_input(f"{label} *", value=default, key=f"param_{selected_name}_{key}")
            else:
                value = st.text_input(f"{label}", value=default, key=f"param_{selected_name}_{key}")

            filled_params[key] = value

    # Build body for POST requests that require it
    if endpoint["method"] == "POST":
        body_params = {k: v for k, v in filled_params.items() if k not in path_params}
        if body_params:
            body = body_params

# ── Destructive action warning ─────────────────────────────────────────────────

is_destructive = endpoint["method"] in ("DELETE", "POST") and "Remove" in selected_name
confirmed = True

if is_destructive:
    st.warning(
        "⚠️ This is a **destructive action** and will modify your team. "
        "Check the box below to confirm before running."
    )
    confirmed = st.checkbox("Yes, I understand — run this action against my live team.")

# ── Run button ─────────────────────────────────────────────────────────────────

run_disabled = not confirmed

if st.button(f"▶  Run  —  {endpoint['method']}  {endpoint['path']}", disabled=run_disabled, type="primary"):
    # Resolve path placeholders
    resolved_path = build_path(endpoint["path"], {k: v for k, v in filled_params.items() if k in path_params})

    with st.spinner("Calling the Tabnine API..."):
        status_code, response_data = make_request(
            token=token,
            method=endpoint["method"],
            path=resolved_path,
            body=body,
        )

    st.markdown("---")
    st.subheader("Response")
    render_response(status_code, response_data)

    # ── cURL equivalent (handy for colleagues) ─────────────────────────────
    st.markdown("---")
    st.subheader("Equivalent cURL command")
    curl_body = f" \\\n  -d '{json.dumps(body)}'" if body else ""
    curl_cmd = (
        f"curl -X {endpoint['method']} \\\n"
        f"  '{BASE_URL}{resolved_path}' \\\n"
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
            "Capability": name,
            "Method": ep["method"],
            "Path": ep["path"],
            "Description": ep["description"],
            "Docs": f"{DOCS_BASE}{ep['doc_anchor']}",
        })
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
