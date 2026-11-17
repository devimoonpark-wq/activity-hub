
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from kpi_rules import get_kpi_rule


# ==========================================
# 1. APP SETTINGS
# ==========================================

st.set_page_config(
    page_title="Activity Hub V2",
    page_icon="📊",
    layout="wide"
)

ROOT = Path(__file__).resolve().parent

KPI_FILE = ROOT / "Activity_Hub_Real_KPI_Sanitized.csv"
ACTIVITY_FILE = ROOT / "Activity_Hub_Activity_Records_V2.csv"


# ==========================================
# 2. LOAD DATA
# ==========================================

@st.cache_data
def load_kpis():
    df = pd.read_csv(KPI_FILE)

    required = {
        "Year", "Month", "Category",
        "Metric", "Value", "Unit"
    }

    missing = required - set(df.columns)

    if missing:
        raise ValueError(
            f"KPI file missing columns: {sorted(missing)}"
        )

    for col in ["Year", "Month", "Value"]:
        df[col] = pd.to_numeric(
            df[col], errors="coerce"
        )

    df = df.dropna(
        subset=["Year", "Month", "Category", "Metric"]
    ).copy()

    df["Year"] = df["Year"].astype(int)
    df["Month"] = df["Month"].astype(int)

    df["Unit"] = (
        df["Unit"]
        .fillna("")
        .astype(str)
        .str.lower()
        .str.strip()
    )

    # Employee survey results are ratings, not counts.
    mask = (
        (df["Category"] == "Employee Engagement")
        & (df["Metric"] == "Review from participants")
    )

    df.loc[mask, "Unit"] = "rating"

    return df


@st.cache_data
def load_activities():
    df = pd.read_csv(ACTIVITY_FILE)

    required = {
        "Activity_ID", "Year", "Month",
        "Category", "Activity_Name", "Status"
    }

    missing = required - set(df.columns)

    if missing:
        raise ValueError(
            f"Activity file missing columns: {sorted(missing)}"
        )

    df["Year"] = pd.to_numeric(
        df["Year"], errors="coerce"
    ).astype("Int64")

    df["Month"] = pd.to_numeric(
        df["Month"], errors="coerce"
    ).astype("Int64")

    return df


# ==========================================
# 3. FORMATTING
# ==========================================

def format_value(value, unit):
    if value is None or pd.isna(value):
        return "N/A"

    value = float(value)

    if unit == "percent":
        return f"{value:.1%}"

    if unit == "count":
        if value.is_integer():
            return f"{value:,.0f}"
        return f"{value:,.2f}".rstrip("0").rstrip(".")

    return f"{value:,.2f}".rstrip("0").rstrip(".")


def month_label(month):
    if pd.isna(month):
        return "Unscheduled"

    month = int(month)

    if not 1 <= month <= 12:
        return "Unscheduled"

    return pd.Timestamp(
        year=2026, month=month, day=1
    ).strftime("%b")


# ==========================================
# 4. KPI CALCULATION
# ==========================================

def summarize(records, rule):
    valid = (
        records.dropna(subset=["Value"])
        .sort_values(["Year", "Month"])
    )

    if valid.empty:
        return None, "No recorded value"

    latest = valid.iloc[-1]

    if rule == "sum":
        return (
            valid["Value"].sum(),
            "Sum of recorded months (not necessarily full year)"
        )

    elif rule == "latest":
        return (
            latest["Value"],
            f"Latest: {month_label(latest['Month'])} "
            f"{int(latest['Year'])}"
        )

    elif rule == "batch":
        if len(valid) == 1:
            return (
                latest["Value"],
                "Batch result (one record)"
            )

        return (
            None,
            "Multiple records. Review batch details."
        )

    elif rule == "event":
        return (
            latest["Value"],
            "Latest recorded event only. See event details below."
        )

    elif rule == "source_required":
        return (
            latest["Value"],
            "Latest monthly snapshot, not an annual average"
        )

    return None, "Calculation rule not defined"


# ==========================================
# 5. LINK EVENT DETAILS
# ==========================================

def event_details(kpi_data, activity_data):

    event_metrics = [
        "Activity participants",
        "Review from participants",
        "Event participants"
    ]

    events = kpi_data[
        kpi_data["Metric"].isin(event_metrics)
    ].copy()

    if events.empty:
        return events

    completed = activity_data[
        activity_data["Status"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.casefold()
        .eq("completed")
    ].copy()

    completed = completed.dropna(
        subset=["Year", "Month", "Category"]
    )

    # Match only when exactly one completed activity
    # exists for the same year, month and category.
    keys = ["Year", "Month", "Category"]

    counts = (
        completed.groupby(keys)
        .size()
        .reset_index(name="Activity_Count")
    )

    completed = completed.merge(
        counts, on=keys, how="left"
    )

    unique_activities = completed[
        completed["Activity_Count"] == 1
    ][keys + ["Activity_Name"]]

    events = events.merge(
        unique_activities,
        on=keys,
        how="left"
    )

    events["Activity_Name"] = (
        events["Activity_Name"].fillna(
            "Activity not uniquely matched. Verify source."
        )
    )

    events["Result"] = events.apply(
        lambda row: format_value(
            row["Value"], row["Unit"]
        ),
        axis=1
    )

    return events


# ==========================================
# 6. INITIALIZE APPLICATION
# ==========================================

try:
    kpis = load_kpis()
    activities = load_activities()

except (
    FileNotFoundError,
    ValueError,
    pd.errors.ParserError
) as error:
    st.error(f"Data loading problem: {error}")
    st.stop()


st.sidebar.title("Activity Hub")

page = st.sidebar.radio(
    "Navigation",
    ["Overview", "Performance", "Activities", "Import Data"]
)

st.title("Activity Hub")

st.caption(
    "Corporate Branding | Performance, activities "
    "and annual reporting"
)


# ==========================================
# 7. OVERVIEW PAGE
# ==========================================

if page == "Overview":

    st.header("Annual Overview")

    years = sorted(
        set(kpis["Year"].unique())
        | set(
            activities["Year"]
            .dropna()
            .astype(int)
            .unique()
        )
    )

    period = st.selectbox(
        "Reporting Period",
        ["All Years"] + years,
        index=len(years)
    )

    if period == "All Years":
        filtered = kpis.copy()
    else:
        filtered = kpis[
            kpis["Year"] == period
        ].copy()

    categories = sorted(
        filtered["Category"].dropna().unique()
    )

    if not categories:
        st.info(
            "No KPI records available for this period. "
            "Check the Activities page for historical records."
        )

    else:
        category = st.selectbox(
            "Category", categories
        )

        search = st.text_input(
            "Search KPI",
            placeholder="Type a metric name..."
        )

        data = filtered[
            filtered["Category"] == category
        ].copy()

        if search:
            data = data[
                data["Metric"].str.contains(
                    search,
                    case=False,
                    na=False,
                    regex=False
                )
            ]

        if data.empty:
            st.info("No KPI matches your search.")

        else:
            st.caption(
                f"{len(data)} KPI records in this selection"
            )

            for year, year_data in data.groupby(
                "Year", sort=True
            ):

                st.subheader(
                    f"{category} | {year}"
                )

                metrics = sorted(
                    year_data["Metric"].unique()
                )

                columns = st.columns(3)

                for i, metric in enumerate(metrics):

                    records = year_data[
                        year_data["Metric"] == metric
                    ].copy()

                    rule = get_kpi_rule(
                        category, metric
                    )

                    value, description = summarize(
                        records, rule
                    )

                    unit = records["Unit"].iloc[-1]

                    with columns[i % 3]:
                        st.metric(
                            label=metric,
                            value=(
                                format_value(value, unit)
                                if value is not None
                                else "N/A"
                            )
                        )

                        st.caption(description)

                # Event-specific results
                if category in [
                    "Employee Engagement",
                    "University Partnership"
                ]:

                    events = event_details(
                        year_data, activities
                    )

                    if not events.empty:

                        st.markdown(
                            "**Individual Event Results**"
                        )

                        display = events[
                            [
                                "Month",
                                "Activity_Name",
                                "Metric",
                                "Result"
                            ]
                        ].sort_values(
                            ["Month", "Metric"]
                        )

                        st.dataframe(
                            display,
                            hide_index=True,
                            width="stretch"
                        )

            with st.expander(
                "View Detailed KPI Records"
            ):

                details = data[
                    [
                        "Year",
                        "Month",
                        "Metric",
                        "Value",
                        "Unit"
                    ]
                ].sort_values(
                    ["Year", "Month"]
                )

                st.dataframe(
                    details,
                    hide_index=True,
                    width="stretch"
                )


# ==========================================
# 8. PERFORMANCE PAGE
# ==========================================

elif page == "Performance":

    st.header("Performance Dashboard")

    years = sorted(kpis["Year"].unique())

    if not years:
        st.info("No KPI data available.")

    else:
        year = st.selectbox(
            "Year",
            years,
            index=len(years) - 1
        )

        year_data = kpis[
            kpis["Year"] == year
        ]

        category = st.selectbox(
            "Category",
            sorted(year_data["Category"].unique())
        )

        available = year_data[
            year_data["Category"] == category
        ]

        metric = st.selectbox(
            "Metric",
            sorted(available["Metric"].unique())
        )

        selected = available[
            available["Metric"] == metric
        ].sort_values("Month").copy()

        selected = selected.dropna(
            subset=["Value"]
        )

        if selected.empty:
            st.info(
                "No values recorded for this selection."
            )

        else:
            unit = selected["Unit"].iloc[-1]

            rule = get_kpi_rule(
                category, metric
            )

            latest = selected.iloc[-1]

            st.metric(
                f"Latest recorded: {metric}",
                format_value(
                    latest["Value"], unit
                )
            )

            st.caption(
                f"{month_label(latest['Month'])} "
                f"{year} | Reporting rule: {rule}"
            )

            if rule == "source_required":
                st.info(
                    "This is a monthly snapshot. "
                    "An official period-level figure is "
                    "needed for annual reporting."
                )

            if rule == "event":
                st.info(
                    "These are individual event results, "
                    "not a combined monthly total."
                )

            selected["Month Label"] = (
                selected["Month"].map(month_label)
            )

            selected["Result"] = selected.apply(
                lambda row: format_value(
                    row["Value"], row["Unit"]
                ),
                axis=1
            )

            st.subheader("Recorded Performance")

            if rule == "event":

                enriched = event_details(
                    selected, activities
                )

                st.dataframe(
                    enriched[
                        [
                            "Month Label",
                            "Activity_Name",
                            "Result"
                        ]
                    ],
                    hide_index=True,
                    width="stretch"
                )

            else:
                st.dataframe(
                    selected[
                        ["Month Label", "Result"]
                    ],
                    hide_index=True,
                    width="stretch"
                )

            # Chart
            chart = selected.copy()

            if unit == "percent":
                chart["Chart Value"] = (
                    chart["Value"] * 100
                )
                y_label = "Percent (%)"

            else:
                chart["Chart Value"] = chart["Value"]
                y_label = metric

            if rule == "event":
                chart["Event Label"] = (
                    chart["Month Label"]
                    + " | Record "
                    + (
                        chart.groupby("Month")
                        .cumcount() + 1
                    ).astype(str)
                )

                fig = px.bar(
                    chart,
                    x="Event Label",
                    y="Chart Value",
                    title=f"{metric} | {year}",
                    labels={
                        "Chart Value": y_label,
                        "Event Label": "Event record"
                    }
                )

            else:
                fig = px.line(
                    chart,
                    x="Month",
                    y="Chart Value",
                    markers=True,
                    title=f"{metric} | {year}",
                    labels={
                        "Chart Value": y_label,
                        "Month": "Month"
                    }
                )

                months = sorted(
                    chart["Month"].unique()
                )

                fig.update_xaxes(
                    tickmode="array",
                    tickvals=months,
                    ticktext=[
                        month_label(m)
                        for m in months
                    ]
                )

            st.plotly_chart(
                fig,
                width="stretch"
            )


# ==========================================
# 9. ACTIVITIES PAGE
# ==========================================

elif page == "Activities":

    st.header("Historical Activities & Plans")

    st.caption(
        f"{len(activities)} activity and initiative "
        "records available"
    )

    years = sorted(
        activities["Year"]
        .dropna()
        .astype(int)
        .unique()
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        year = st.selectbox(
            "Year",
            ["All Years"] + years
        )

    with col2:
        category = st.selectbox(
            "Category",
            ["All Categories"]
            + sorted(
                activities["Category"]
                .dropna()
                .unique()
            )
        )

    with col3:
        status = st.selectbox(
            "Status",
            ["All Statuses"]
            + sorted(
                activities["Status"]
                .dropna()
                .unique()
            )
        )

    search = st.text_input(
        "Search Activities",
        placeholder="Name, goal or details..."
    )

    data = activities.copy()

    if year != "All Years":
        data = data[
            data["Year"] == year
        ]

    if category != "All Categories":
        data = data[
            data["Category"] == category
        ]

    if status != "All Statuses":
        data = data[
            data["Status"] == status
        ]

    if search:
        search_columns = [
            col for col in [
                "Activity_Name",
                "Goal",
                "Details"
            ]
            if col in data.columns
        ]

        text = (
            data[search_columns]
            .fillna("")
            .astype(str)
            .agg(" ".join, axis=1)
        )

        data = data[
            text.str.contains(
                search,
                case=False,
                regex=False
            )
        ]

    completed = (
        data["Status"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.casefold()
        .eq("completed")
        .sum()
    )

    a, b, c = st.columns(3)

    a.metric("Matching Records", len(data))
    b.metric("Completed", int(completed))
    c.metric(
        "Other Statuses",
        len(data) - int(completed)
    )

    st.caption(
        "Activity statuses are based on source data."
    )

    st.subheader("Activity Records")

    for _, record in data.sort_values(
        ["Year", "Month", "Activity_Name"],
        na_position="last"
    ).iterrows():

        year_text = (
            str(int(record["Year"]))
            if pd.notna(record["Year"])
            else "Unknown"
        )

        title = (
            f"{year_text} | "
            f"{month_label(record['Month'])} | "
            f"{record['Activity_Name']}"
        )

        with st.expander(title):

            st.write(
                f"**Category:** {record['Category']}"
            )

            st.write(
                f"**Status:** {record['Status']}"
            )

            for field in ["Goal", "Details"]:
                if (
                    field in record.index
                    and pd.notna(record[field])
                    and str(record[field]).strip()
                ):
                    st.write(
                        f"**{field}:** {record[field]}"
                    )

            if (
                pd.notna(record["Year"])
                and pd.notna(record["Month"])
            ):

                related_kpis = kpis[
                    (kpis["Year"] == int(record["Year"]))
                    & (
                        kpis["Month"]
                        == int(record["Month"])
                    )
                    & (
                        kpis["Category"]
                        == record["Category"]
                    )
                ]

                related = event_details(
                    related_kpis, activities
                )

                if not related.empty:
                    related = related[
                        related["Activity_Name"]
                        == record["Activity_Name"]
                    ]

                if not related.empty:
                    st.write("**Linked KPI Results**")

                    st.dataframe(
                        related[["Metric", "Result"]],
                        hide_index=True,
                        width="stretch"
                    )

    with st.expander("View Source Activity Table"):
        st.dataframe(
            data,
            hide_index=True,
            width="stretch"
        )


# ==========================================
# 10. IMPORT DATA PAGE
# ==========================================

elif page == "Import Data":

    st.header("Import Data | Preview Only")

    st.info(
        "Uploaded files are checked and previewed. "
        "They do not automatically replace saved data."
    )

    kind = st.radio(
        "Data Type",
        ["KPI records", "Activity records"]
    )

    uploaded = st.file_uploader(
        "Choose CSV or Excel",
        type=["csv", "xlsx"]
    )

    if uploaded is not None:

        try:
            if uploaded.name.lower().endswith(".csv"):
                preview = pd.read_csv(uploaded)
            else:
                preview = pd.read_excel(uploaded)

            if kind == "KPI records":
                required = {
                    "Year", "Month", "Category",
                    "Metric", "Value", "Unit"
                }
            else:
                required = {
                    "Activity_ID", "Year", "Month",
                    "Category", "Activity_Name", "Status"
                }

            missing = required - set(
                preview.columns
            )

            if missing:
                st.error(
                    "Missing required columns: "
                    + ", ".join(sorted(missing))
                )

            else:
                st.success(
                    f"{len(preview)} rows passed "
                    "the column check."
                )

                st.dataframe(
                    preview.head(30),
                    hide_index=True,
                    width="stretch"
                )

                st.download_button(
                    "Download Reviewed CSV",
                    data=preview.to_csv(
                        index=False
                    ).encode("utf-8"),
                    file_name="reviewed_upload.csv",
                    mime="text/csv"
                )

                st.warning(
                    "This is a preview, not an automatic "
                    "import. Back up your existing file "
                    "before manually replacing it."
                )

        except Exception as error:
            st.error(
                f"Unable to read upload: {error}"
            )
