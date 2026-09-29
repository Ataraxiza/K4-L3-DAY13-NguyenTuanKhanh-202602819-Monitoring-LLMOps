from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.challenge import load_challenge

LOG_PATH = REPO_ROOT / "data" / "logs.jsonl"
CONFIG_PATH = REPO_ROOT / "config" / "dashboard.yaml"
CHALLENGE_PATH = REPO_ROOT / "config" / "challenge.json"

st.set_page_config(
    page_title="Day 13 | Monitoring",
    page_icon="📈",
    layout="wide",
)


# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------

st.markdown(
    """
    <style>
    .stApp {
        background: #0f1714;
        color: #e7efeb;
    }

    [data-testid="stHeader"] {
        background: rgba(15, 23, 20, 0.92);
    }

    [data-testid="stSidebar"] {
        background: #16211d;
        border-right: 1px solid #2a3933;
    }

    h1, h2, h3 {
        color: #e8f1ed;
    }

    p, label, .stCaption {
        color: #b9c8c1;
    }

    [data-testid="stMetric"] {
        background: #17221e;
        border: 1px solid #2a3933;
        padding: 12px 14px;
        border-radius: 6px;
    }

    [data-testid="stMetricLabel"] {
        color: #9fb1a8;
    }

    [data-testid="stMetricValue"] {
        color: #f0f7f3;
    }

    [data-testid="stPlotlyChart"] {
        background: #17221e;
        border: 1px solid #2a3933;
        border-radius: 6px;
        padding: 5px;
    }

    [data-testid="stDataFrame"] {
        border: 1px solid #2a3933;
        border-radius: 6px;
    }

    .stSelectbox > div > div {
        background: #17221e;
        color: #e7efeb;
        border-color: #35463f;
    }

    .stAlert {
        background: #18251f;
        border-color: #35463f;
        color: #dce8e2;
    }

    hr {
        border-color: #2a3933;
    }
    </style>
    """,
    unsafe_allow_html=True,
)



# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

@st.cache_data(ttl=10)
def read_config() -> dict:
    with CONFIG_PATH.open(encoding="utf-8") as config_file:
        return yaml.safe_load(config_file)["dashboard"]


@st.cache_data(ttl=10)
def read_logs() -> pd.DataFrame:
    records: list[dict] = []

    if not LOG_PATH.exists():
        return pd.DataFrame()

    with LOG_PATH.open(encoding="utf-8") as log_file:
        for line in log_file:
            line = line.strip()

            if not line:
                continue

            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    frame = pd.DataFrame(records)

    if frame.empty:
        return frame

    if "ts" in frame.columns:
        frame["ts"] = pd.to_datetime(
            frame["ts"],
            utc=True,
            errors="coerce",
        )

        frame = (
            frame
            .dropna(subset=["ts"])
            .sort_values("ts")
            .reset_index(drop=True)
        )

    return frame


def numeric(frame: pd.DataFrame, field: str) -> pd.Series:
    if field not in frame.columns:
        return pd.Series(dtype="float64")

    return pd.to_numeric(
        frame[field],
        errors="coerce",
    ).dropna()


def threshold_for(config: dict, panel_id: str) -> dict:
    for panel in config["panels"]:
        if panel["id"] == panel_id:
            return panel["threshold"]

    raise KeyError(f"Panel not found: {panel_id}")


def incident_threshold(config: dict) -> int:
    try:
        return load_challenge(CHALLENGE_PATH).latency_threshold_ms
    except (FileNotFoundError, ValueError):
        return int(threshold_for(config, "latency")["value"])


def percentile(
    frame: pd.DataFrame,
    field: str,
    value: float,
) -> float | None:
    values = numeric(frame, field)

    if values.empty:
        return None

    return float(values.quantile(value / 100))


def mean_value(
    frame: pd.DataFrame,
    field: str,
) -> float | None:
    values = numeric(frame, field)

    if values.empty:
        return None

    return float(values.mean())


def sum_value(
    frame: pd.DataFrame,
    field: str,
) -> float | None:
    values = numeric(frame, field)

    if values.empty:
        return None

    return float(values.sum())


def rate_pct(
    numerator: int,
    denominator: int,
) -> float | None:
    if denominator == 0:
        return None

    return numerator / denominator * 100


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------

def format_value(
    value: float | None,
    unit: str,
) -> str:
    if value is None:
        return "No data"

    if unit == "ms":
        return f"{value:,.0f} ms"

    if unit == "usd":
        return f"${value:,.4f}"

    if unit == "percent":
        return f"{value:.2f}%"

    if unit == "score_0_to_1":
        return f"{value:.3f}"

    if unit == "requests_per_minute":
        return f"{value:.2f} req/min"

    if unit == "tokens":
        return f"{value:,.0f}"

    return f"{value:,.2f}"


# ---------------------------------------------------------------------------
# Plot helpers
# ---------------------------------------------------------------------------

def style_figure(
    fig: go.Figure,
    y_title: str,
) -> go.Figure:
    fig.update_layout(
        height=280,
        margin=dict(
            l=12,
            r=18,
            t=35,
            b=12,
        ),
        paper_bgcolor="#17221e",
        plot_bgcolor="#17221e",
        font=dict(
            color="#dce8e2",
            family="Aptos, Segoe UI, sans-serif",
            size=12,
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            x=0,
            font=dict(color="#c4d2cb"),
        ),
        hovermode="x unified",
    )

    fig.update_xaxes(
        showgrid=False,
        title=None,
        color="#aebeb6",
        linecolor="#35463f",
    )

    fig.update_yaxes(
        title=y_title,
        gridcolor="#293831",
        zerolinecolor="#35463f",
        color="#aebeb6",
    )

    return fig

def add_threshold(
    fig: go.Figure,
    value: float,
    label: str,
) -> None:
    fig.add_hline(
        y=value,
        line_dash="dash",
        line_color="#d05b45",
        annotation_text=label,
        annotation_position="top left",
    )


def minute_count(frame: pd.DataFrame) -> pd.Series:
    if frame.empty or "ts" not in frame.columns:
        return pd.Series(dtype="float64")

    return (
        frame
        .set_index("ts")
        .resample("1min")
        .size()
        .astype(float)
    )


def minute_sum(
    frame: pd.DataFrame,
    field: str,
) -> pd.Series:
    if frame.empty or field not in frame.columns:
        return pd.Series(dtype="float64")

    values = frame[["ts", field]].copy()

    values[field] = pd.to_numeric(
        values[field],
        errors="coerce",
    )

    values = values.dropna(subset=[field])

    if values.empty:
        return pd.Series(dtype="float64")

    return (
        values
        .set_index("ts")[field]
        .resample("1min")
        .sum()
    )


def minute_mean(
    frame: pd.DataFrame,
    field: str,
) -> pd.Series:
    if frame.empty or field not in frame.columns:
        return pd.Series(dtype="float64")

    values = frame[["ts", field]].copy()

    values[field] = pd.to_numeric(
        values[field],
        errors="coerce",
    )

    values = values.dropna(subset=[field])

    if values.empty:
        return pd.Series(dtype="float64")

    return (
        values
        .set_index("ts")[field]
        .resample("1min")
        .mean()
    )


def minute_percentile(
    frame: pd.DataFrame,
    field: str,
    percentile_value: int,
) -> pd.Series:
    if frame.empty or field not in frame.columns:
        return pd.Series(dtype="float64")

    values = frame[["ts", field]].copy()

    values[field] = pd.to_numeric(
        values[field],
        errors="coerce",
    )

    values = values.dropna(subset=[field])

    if values.empty:
        return pd.Series(dtype="float64")

    return (
        values
        .set_index("ts")[field]
        .resample("1min")
        .quantile(percentile_value / 100)
    )


def show_panel(
    title: str,
    unit: str,
    threshold: dict,
    value: float | None,
    fig: go.Figure,
) -> None:
    comparator = (
        "≤"
        if threshold["operator"] == "lte"
        else "≥"
    )

    st.subheader(title)

    st.caption(
        f"Unit: {unit} · "
        f"Threshold: "
        f"{threshold['aggregation']} "
        f"{comparator} "
        f"{threshold['value']:g} "
        f"{unit}"
    )

    st.metric(
        "Current window",
        format_value(value, unit),
    )

    st.plotly_chart(
        fig,
        width="stretch",
    )


# ---------------------------------------------------------------------------
# Six dashboard panels
# ---------------------------------------------------------------------------

def render_dashboard(
    config: dict,
    window: pd.DataFrame,
    all_logs: pd.DataFrame,
) -> None:

    events = window.get(
        "event",
        pd.Series(
            index=window.index,
            dtype="string",
        ),
    )

    responses = window[
        events == "response_sent"
    ].copy()

    requests = window[
        events == "request_received"
    ].copy()

    failures = window[
        events == "request_failed"
    ].copy()

    st.title(config["title"])

    latest = (
        all_logs["ts"].max().strftime(
            "%Y-%m-%d %H:%M:%S UTC"
        )
        if not all_logs.empty
        else "no log records"
    )

    st.caption(
        f"Source: data/logs.jsonl · "
        f"Default window: {config['time_range_minutes']} min · "
        f"Refresh: {config['refresh_seconds']} sec · "
        f"Latest record: {latest}"
    )

    if window.empty:
        st.warning(
            "No log records fall within this time range."
        )
        return

    # ============================================================
    # PANEL 1 — LATENCY
    # ============================================================

    latency_threshold = threshold_for(
        config,
        "latency",
    )

    latency_fig = go.Figure()

    for p, color in (
        (50, "#4276a5"),
        (95, "#177e70"),
        (99, "#d05b45"),
    ):
        values = minute_percentile(
            responses,
            "latency_ms",
            p,
        )

        if not values.empty:
            latency_fig.add_trace(
                go.Scatter(
                    x=values.index,
                    y=values.values,
                    name=f"P{p}",
                    mode="lines+markers",
                    line=dict(
                        color=color,
                        width=2,
                    ),
                )
            )

    ttft = minute_percentile(
        responses,
        "ttft_ms",
        95,
    )

    if not ttft.empty:
        latency_fig.add_trace(
            go.Scatter(
                x=ttft.index,
                y=ttft.values,
                name="TTFT P95",
                mode="lines+markers",
                line=dict(
                    color="#d28a31",
                    width=2,
                ),
            )
        )

    add_threshold(
        latency_fig,
        latency_threshold["value"],
        f"P95 limit {latency_threshold['value']} ms",
    )

    style_figure(
        latency_fig,
        "Milliseconds",
    )

    # ============================================================
    # PANEL 2 — TRAFFIC
    # ============================================================

    traffic_threshold = threshold_for(
        config,
        "traffic",
    )

    traffic = minute_count(requests)

    traffic_rate = (
        float(traffic.mean())
        if not traffic.empty
        else None
    )

    traffic_fig = go.Figure()

    if not traffic.empty:
        traffic_fig.add_trace(
            go.Bar(
                x=traffic.index,
                y=traffic.values,
                name="Requests/min",
                marker_color="#177e70",
            )
        )

    add_threshold(
        traffic_fig,
        traffic_threshold["value"],
        f"Minimum {traffic_threshold['value']} req/min",
    )

    style_figure(
        traffic_fig,
        "Requests/minute",
    )

    # ============================================================
    # PANEL 3 — ERRORS + RETRIEVAL SUCCESS
    # ============================================================

    error_threshold = threshold_for(
        config,
        "errors",
    )

    errors_by_minute = minute_count(
        failures
    )

    requests_by_minute = minute_count(
        requests
    )

    error_fig = go.Figure()

    if not requests_by_minute.empty:
        aligned_errors = errors_by_minute.reindex(
            requests_by_minute.index,
            fill_value=0,
        )

        error_rate_series = (
            aligned_errors
            / requests_by_minute
            * 100
        )

        error_fig.add_trace(
            go.Scatter(
                x=error_rate_series.index,
                y=error_rate_series.values,
                name="Error rate",
                mode="lines+markers",
                line=dict(
                    color="#d05b45",
                    width=2,
                ),
            )
        )

    tool_success = (
        responses.get(
            "tool_success",
            pd.Series(
                index=responses.index,
                dtype="object",
            ),
        )
        .astype(str)
        .str.lower()
    )

    retrieval_success = (
        responses.assign(
            retrieval_success=tool_success.eq("true")
        )
        .set_index("ts")["retrieval_success"]
        .resample("1min")
        .mean()
        * 100
    )

    if not retrieval_success.empty:
        error_fig.add_trace(
            go.Scatter(
                x=retrieval_success.index,
                y=retrieval_success.values,
                name="Retrieval success",
                mode="lines+markers",
                line=dict(
                    color="#4276a5",
                    width=2,
                ),
            )
        )

    add_threshold(
        error_fig,
        error_threshold["value"],
        f"Error limit {error_threshold['value']}%",
    )

    style_figure(
        error_fig,
        "Percent",
    )

    error_rate = rate_pct(
        len(failures),
        len(requests),
    )

    retrieval_success_rate = (
        float(tool_success.eq("true").mean() * 100)
        if not tool_success.empty
        else None
    )

    # ============================================================
    # PANEL 4 — COST
    # ============================================================

    cost_threshold = threshold_for(
        config,
        "cost",
    )

    cost_by_minute = minute_sum(
        responses,
        "cost_usd",
    )

    total_cost = sum_value(
        responses,
        "cost_usd",
    )

    cost_fig = go.Figure()

    if not cost_by_minute.empty:
        cost_fig.add_trace(
            go.Scatter(
                x=cost_by_minute.index,
                y=cost_by_minute.values,
                name="Cost/min",
                mode="lines+markers",
                line=dict(
                    color="#177e70",
                    width=2,
                ),
            )
        )

    add_threshold(
        cost_fig,
        cost_threshold["value"],
        f"Limit ${cost_threshold['value']:g}",
    )

    style_figure(
        cost_fig,
        "USD/minute",
    )

    # ============================================================
    # PANEL 5 — TOKENS
    # ============================================================

    token_threshold = threshold_for(
        config,
        "tokens",
    )

    input_tokens = minute_sum(
        responses,
        "tokens_in",
    )

    output_tokens = minute_sum(
        responses,
        "tokens_out",
    )

    tokens_fig = go.Figure()

    if not input_tokens.empty:
        tokens_fig.add_trace(
            go.Scatter(
                x=input_tokens.index,
                y=input_tokens.values,
                name="Input tokens/min",
                mode="lines+markers",
                line=dict(
                    color="#4276a5",
                    width=2,
                ),
            )
        )

    if not output_tokens.empty:
        tokens_fig.add_trace(
            go.Scatter(
                x=output_tokens.index,
                y=output_tokens.values,
                name="Output tokens/min",
                mode="lines+markers",
                line=dict(
                    color="#d28a31",
                    width=2,
                ),
            )
        )

    add_threshold(
        tokens_fig,
        token_threshold["value"],
        f"Limit {token_threshold['value']:,}",
    )

    style_figure(
        tokens_fig,
        "Tokens/minute",
    )

    total_input_tokens = sum_value(
        responses,
        "tokens_in",
    )

    total_output_tokens = sum_value(
        responses,
        "tokens_out",
    )

    token_display_value = (
        max(
            total_input_tokens or 0,
            total_output_tokens or 0,
        )
        if not responses.empty
        else None
    )

    # ============================================================
    # PANEL 6 — QUALITY
    # ============================================================

    quality_threshold = threshold_for(
        config,
        "quality",
    )

    quality_by_minute = minute_mean(
        responses,
        "quality_score",
    )

    quality_mean = mean_value(
        responses,
        "quality_score",
    )

    quality_fig = go.Figure()

    if not quality_by_minute.empty:
        quality_fig.add_trace(
            go.Scatter(
                x=quality_by_minute.index,
                y=quality_by_minute.values,
                name="Mean quality",
                mode="lines+markers",
                line=dict(
                    color="#177e70",
                    width=2,
                ),
            )
        )

    add_threshold(
        quality_fig,
        quality_threshold["value"],
        f"Minimum {quality_threshold['value']:g}",
    )

    style_figure(
        quality_fig,
        "Score (0–1)",
    )

    # ============================================================
    # RENDER EXACTLY SIX PANELS
    # ============================================================

    row1 = st.columns(2, gap="large")

    with row1[0]:
        show_panel(
            "1. Latency",
            "ms",
            latency_threshold,
            percentile(
                responses,
                "latency_ms",
                95,
            ),
            latency_fig,
        )

    with row1[1]:
        show_panel(
            "2. Traffic",
            "requests_per_minute",
            traffic_threshold,
            traffic_rate,
            traffic_fig,
        )

    row2 = st.columns(2, gap="large")

    with row2[0]:
        show_panel(
            "3. Errors",
            "percent",
            error_threshold,
            error_rate,
            error_fig,
        )

        st.caption(
            f"Retrieval success: "
            f"{format_value(retrieval_success_rate, 'percent')}"
        )

    with row2[1]:
        show_panel(
            "4. Cost",
            "usd",
            cost_threshold,
            total_cost,
            cost_fig,
        )

    row3 = st.columns(2, gap="large")

    with row3[0]:
        show_panel(
            "5. Tokens",
            "tokens",
            token_threshold,
            token_display_value,
            tokens_fig,
        )

        st.caption(
            f"Input total: "
            f"{total_input_tokens or 0:,.0f} · "
            f"Output total: "
            f"{total_output_tokens or 0:,.0f}"
        )

    with row3[1]:
        show_panel(
            "6. Quality",
            "score_0_to_1",
            quality_threshold,
            quality_mean,
            quality_fig,
        )

    # ============================================================
    # INCIDENT DRILL-DOWN
    # This is NOT counted as a seventh dashboard panel.
    # ============================================================

    st.divider()
    st.subheader("Incident drill-down")
    incident_threshold_ms = incident_threshold(config)
    st.caption(
        f"Incident latency threshold: {incident_threshold_ms} ms. "
        "The latency panel retains its dashboard SLO threshold."
    )

    latency_col = pd.to_numeric(
        window.get(
            "latency_ms",
            pd.Series(
                index=window.index,
                dtype="float64",
            ),
        ),
        errors="coerce",
    )

    tool_success_col = (
        window.get(
            "tool_success",
            pd.Series(
                index=window.index,
                dtype="object",
            ),
        )
        .astype(str)
        .str.lower()
    )

    abnormal = window[
        (events == "request_failed")
        |
        (
            (events == "response_sent")
            &
            (latency_col > incident_threshold_ms)
        )
        |
        (
            (events == "response_sent")
            &
            (tool_success_col == "false")
        )
    ].copy()

    if abnormal.empty:
        st.info(
            "No failed, over-threshold, or unsuccessful-retrieval "
            "records in this window."
        )
    else:
        display_fields = [
            field
            for field in (
                "ts",
                "event",
                "correlation_id",
                "latency_ms",
                "error_type",
                "tool_name",
                "tool_success",
                "model",
                "feature",
            )
            if field in abnormal.columns
        ]

        abnormal["ts"] = abnormal["ts"].dt.strftime(
            "%Y-%m-%d %H:%M:%S UTC"
        )

        st.dataframe(
            abnormal[
                display_fields
            ].sort_values(
                "ts",
                ascending=False,
            ),
            hide_index=True,
            width="stretch",
        )

        st.caption(
            "Use correlation_id to locate the matching "
            "trace in your personal Langfuse project."
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    config = read_config()

    st.sidebar.header(
        "Dashboard controls"
    )

    choices = {
        "Last 60 minutes": pd.Timedelta(minutes=60),
        "Last 24 hours": pd.Timedelta(hours=24),
        "Last 7 days": pd.Timedelta(days=7),
        "All available data": None,
    }

    selected_range = st.sidebar.selectbox(
        "Time range",
        list(choices),
        index=0,
    )

    st.sidebar.caption(
        f"Auto-refresh: "
        f"{config['refresh_seconds']} seconds"
    )

    st.sidebar.caption(
        "Thresholds are loaded from "
        "config/dashboard.yaml."
    )

    logs = read_logs()

    if logs.empty:
        st.title(config["title"])
        st.warning(
            "No valid structured log records found "
            "in data/logs.jsonl."
        )
        return

    duration = choices[selected_range]

    if duration is None:
        window = logs.copy()
    else:
        cutoff = (
            pd.Timestamp.now(tz="UTC")
            - duration
        )

        window = logs[
            logs["ts"] >= cutoff
        ].copy()

    render_dashboard(
        config,
        window,
        logs,
    )


if __name__ == "__main__":
    main()
