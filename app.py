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
        "query_params": [],
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


def _metric_card(label: str, value, delta=None, suffix: str = "") -> None:
    """Render a single st.metric tile, formatting large numbers with commas."""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        formatted = f"{value:,.0f}{suffix}" if isinstance(value, int) else f"{value:,.2f}{suffix}"
    else:
        formatted = str(value)
    st.metric(label=label, value=formatted, delta=delta)


def _render_usage_dashboard(data: dict, endpoint: dict) -> None:
    """Render usage response as BI metric tiles + charts."""
    usage_block = data.get("usage", data)
    items = usage_block.get("data", [])
    if not items:
        st.warning("No data points returned for the selected date range.")
        return

    # ── Aggregate totals across all data points ────────────────────────────
    def _sum(key, nested=None):
        total = 0
        for item in items:
            src = item.get(nested, item) if nested else item
            total += src.get(key, 0) if isinstance(src, dict) else 0
        return total

    is_v2 = "v2" in endpoint.get("path", "")

    st.subheader("Summary")
    if is_v2:
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1: _metric_card("Active Users", _sum("activeUsers"))
        with c2: _metric_card("Tokens Consumed", _sum("totalTokensConsumed"))
        with c3: _metric_card("Input Tokens", _sum("totalInputTokens"))
        with c4: _metric_card("Output Tokens", _sum("totalOutputTokens"))
        with c5: _metric_card("Total Cost", _sum("totalCost"), suffix=" $")
    else:
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        with c1: _metric_card("Active Users", _sum("activeUsers"))
        with c2: _metric_card("Completions", _sum("completions", "codeCompletions"))
        with c3: _metric_card("Chars Completed", _sum("charsCompleted", "codeCompletions"))
        with c4: _metric_card("Chat Interactions", _sum("interactions", "chat"))
        with c5: _metric_card("Agent Interactions", _sum("interactions", "agent"))
        with c6: _metric_card("Automation Factor", round(_sum("automationFactor", "codeCompletions") / max(len(items), 1), 2))

    # ── Time-series chart (only meaningful when multiple data points) ──────
    if len(items) > 1:
        st.subheader("Trend")
        df_trend = pd.DataFrame(items)
        df_trend["from"] = pd.to_datetime(df_trend["from"], errors="coerce")

        if is_v2 and "totalTokensConsumed" in df_trend.columns:
            fig = px.line(df_trend, x="from", y=["totalTokensConsumed", "totalInputTokens", "totalOutputTokens"],
                          labels={"value": "Tokens", "from": "Date", "variable": "Metric"},
                          title="Token Consumption Over Time")
        elif "activeUsers" in df_trend.columns:
            y_cols = [c for c in ["activeUsers"] if c in df_trend.columns]
            fig = px.bar(df_trend, x="from", y=y_cols,
                         labels={"value": "Count", "from": "Date", "variable": "Metric"},
                         title="Active Users Over Time", barmode="group")
        else:
            fig = None

        if fig:
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              font_color="#F8FAFC", legend_title_text="")
            st.plotly_chart(fig, use_container_width=True)

    # ── Model breakdown chart (v2 only) ───────────────────────────────────
    if is_v2:
        model_rows = []
        for item in items:
            for mb in item.get("modelBreakdown", []):
                model_rows.append(mb)
        if model_rows:
            st.subheader("Model Breakdown")
            df_models = pd.DataFrame(model_rows)
            if "model" in df_models.columns and "tokensConsumed" in df_models.columns:
                agg = df_models.groupby("model", as_index=False)["tokensConsumed"].sum()
                fig2 = px.pie(agg, names="model", values="tokensConsumed",
                              title="Tokens by Model", hole=0.4)
                fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#F8FAFC")
                st.plotly_chart(fig2, use_container_width=True)

    # ── Data table ────────────────────────────────────────────────────────
    st.subheader("Data Table")
    df_flat = pd.json_normalize(items)
    st.dataframe(df_flat, use_container_width=True, hide_index=True)


def _render_list(data: list) -> None:
    """Render a list response as a searchable, styled dataframe."""
    if not data:
        st.info("Empty list returned.")
        return
    df = pd.json_normalize(data)
    total = len(df)
    search = st.text_input("Filter rows", placeholder="Type to search across all columns…", key="_list_search")
    if search:
        mask = df.apply(lambda col: col.astype(str).str.contains(search, case=False, na=False)).any(axis=1)
        df = df[mask]
    st.caption(f"Showing {len(df)} of {total} rows")
    st.dataframe(df, use_container_width=True, hide_index=True)


def _render_object(data: dict) -> None:
    """Render a single-object response as a key-value info card grid."""
    flat = pd.json_normalize(data).to_dict(orient="records")
    if not flat:
        st.json(data)
        return
    items = list(flat[0].items())
    cols = st.columns(min(len(items), 4))
    for i, (k, v) in enumerate(items):
        with cols[i % len(cols)]:
            label = k.replace("_", " ").replace(".", " › ").title()
            if isinstance(v, bool):
                st.metric(label, "Yes" if v else "No")
            elif isinstance(v, (int, float)) and not isinstance(v, bool):
                st.metric(label, f"{v:,}")
            elif isinstance(v, list):
                st.metric(label, f"{len(v)} items")
            else:
                st.metric(label, str(v) if v is not None else "—")


def render_response(code: int, data: dict | list, endpoint: dict | None = None) -> None:
    """Smart renderer: BI dashboard for usage, table for lists, cards for objects."""
    st.markdown(f"**Status:** {status_badge(code)}")

    if code == 0 or not (200 <= code < 300):
        st.json(data)
        return

    ep = endpoint or {}
    path = ep.get("path", "")

    # ── Route to the right renderer ───────────────────────────────────────
    rendered_smart = False

    if "usage" in path and isinstance(data, dict):
        tab_bi, tab_raw = st.tabs(["Dashboard", "Raw JSON"])
        with tab_bi:
            _render_usage_dashboard(data, ep)
        with tab_raw:
            st.json(data)
        rendered_smart = True

    elif isinstance(data, list):
        tab_table, tab_raw = st.tabs(["Table", "Raw JSON"])
        with tab_table:
            _render_list(data)
        with tab_raw:
            st.json(data)
        rendered_smart = True

    elif isinstance(data, dict):
        # Lists nested under common keys
        list_key = next((k for k in ("data", "items", "users", "teams", "results") if k in data and isinstance(data[k], list)), None)
        if list_key:
            tab_table, tab_raw = st.tabs(["Table", "Raw JSON"])
            with tab_table:
                meta = {k: v for k, v in data.items() if k != list_key}
                if meta:
                    meta_cols = st.columns(min(len(meta), 4))
                    for i, (k, v) in enumerate(meta.items()):
                        with meta_cols[i % len(meta_cols)]:
                            st.metric(k.replace("_", " ").title(), str(v))
                _render_list(data[list_key])
            with tab_raw:
                st.json(data)
            rendered_smart = True

    if not rendered_smart:
        tab_cards, tab_raw = st.tabs(["Overview", "Raw JSON"])
        with tab_cards:
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
            # Auto-fill organizationId from the verified org fetched at login
            if key == "organizationId" and not default:
                default = st.session_state.get("org_id", "")
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
