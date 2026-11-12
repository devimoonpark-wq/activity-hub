
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Activity Hub",
    page_icon="📊",
    layout="wide"
)

st.title("Activity Hub")
st.caption("Corporate Branding Performance Dashboard")

st.sidebar.title("Navigation")

page = st.sidebar.radio(
    "Go to",
    ["Overview", "Performance", "Activities", "Import Data"]
)


if page == "Overview":
    st.header("Annual Overview")

    df = pd.read_csv("Activity_Hub_Real_KPI_Sanitized.csv")

    # Prepare available reporting years
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df["Value"] = pd.to_numeric(df["Value"], errors="coerce")
    df["Month"] = pd.to_numeric(df["Month"], errors="coerce")

    years = sorted(df["Year"].dropna().astype(int).unique())

    period = st.selectbox(
        "Reporting Period",
        ["All Years"] + years,
        index=len(years)
    )

    if period == "All Years":
        filtered = df.copy()
    else:
        filtered = df[df["Year"] == period].copy()

    if filtered.empty:
        st.info("No records available for this period.")
        st.stop()

    st.caption(
        f"{len(filtered)} monthly KPI records available"
    )

    st.subheader("Performance by Category")

    # Format each metric according to its unit
    def format_kpi(value, unit):
        if unit == "percent":
            return f"{value:.1%}"
        elif unit == "count":
            return f"{value:,.0f}"
        else:
            return f"{value:,.2f}".rstrip("0").rstrip(".")

    # Show the latest recorded value for each metric
    latest_records = (
        filtered.sort_values(["Year", "Month"])
        .groupby(["Category", "Metric"], as_index=False)
        .tail(1)
    )

    for category in sorted(latest_records["Category"].unique()):
        st.markdown(f"### {category}")

        category_data = latest_records[
            latest_records["Category"] == category
        ]

        columns = st.columns(3)

        for i, (_, record) in enumerate(category_data.iterrows()):
            with columns[i % 3]:
                st.metric(
                    label=record["Metric"],
                    value=format_kpi(
                        record["Value"],
                        record["Unit"]
                    )
                )

    st.divider()

    st.subheader("Available KPI Records")

    summary = filtered[
        ["Year", "Month", "Category", "Metric", "Value", "Unit"]
    ].sort_values(["Year", "Month"])

    st.dataframe(
        summary,
        hide_index=True,
        use_container_width=True
    )

elif page == "Performance":
    st.header("Performance Dashboard")

    df = pd.read_csv("Activity_Hub_Real_KPI_Sanitized.csv")

    year = st.selectbox(
        "Year",
        sorted(df["Year"].dropna().unique())
    )

    year_data = df[df["Year"] == year]

    if year_data.empty:
        st.info("No performance data available for this year.")
        st.stop()

    category = st.selectbox(
        "Category",
        sorted(year_data["Category"].dropna().unique())
    )

    available = year_data[
        year_data["Category"] == category
    ]

    metric = st.selectbox(
        "Metric",
        sorted(available["Metric"].dropna().unique())
    )

    selected = available[
        available["Metric"] == metric
    ].sort_values("Month").copy()

    if selected.empty:
        st.info("No records available for this selection.")
        st.stop()

    unit = selected["Unit"].iloc[0]

    # Format values without changing the original data
    def format_value(value):
        if unit == "percent":
            return f"{value:.1%}"
        elif unit == "count":
            return f"{value:,.0f}"
        else:
            return f"{value:,.2f}".rstrip("0").rstrip(".")

    selected["Result"] = selected["Value"].apply(format_value)

    latest = selected.iloc[-1]

    st.metric(
        label=f"Latest: {metric}",
        value=latest["Result"]
    )

    st.subheader("Monthly Performance")

    display_data = selected[["Month", "Result"]].copy()
    display_data["Month"] = (
        display_data["Month"].astype(str).str.zfill(2)
    )

    st.dataframe(
        display_data,
        hide_index=True,
        use_container_width=True
    )

    chart_data = selected.copy()

    if unit == "percent":
        chart_data["Chart Value"] = chart_data["Value"] * 100
        y_label = "Percentage (%)"
    else:
        chart_data["Chart Value"] = chart_data["Value"]
        y_label = metric

    chart_data["Month"] = (
        chart_data["Month"].astype(str).str.zfill(2)
    )

    fig = px.line(
        chart_data,
        x="Month",
        y="Chart Value",
        markers=True,
        labels={"Chart Value": y_label},
        title=f"{metric} | {year}"
    )

    st.plotly_chart(fig, use_container_width=True)

elif page == "Activities":
    st.header("Historical Activities")
    st.info("Your activity records will appear here.")

elif page == "Import Data":
    st.header("Import Excel")
    st.file_uploader(
        "Upload your master spreadsheet",
        type=["xlsx"]
    )