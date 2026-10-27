import io
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

from backend import load_dataset, run_privacy_pipeline


# ==========================================================
# PAGE SETTINGS
# ==========================================================

st.set_page_config(
    page_title="Privacy Guard AI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ==========================================================
# SESSION STATE
# ==========================================================

defaults = {
    "page": "Dashboard",
    "source_df": None,
    "filename": None,
    "result": None,
    "history": [],
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ==========================================================
# CUSTOM CSS: READABLE TEXT AND CLEAR INTERFACE
# ==========================================================

st.markdown(
    """
    <style>
    @import url(
        'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap'
    );

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        font-size: 15px;
    }

    .stApp {
        background: #0B1020;
        color: #F1F5F9;
    }

    [data-testid="stHeader"] {
        background: #0B1020;
    }

    [data-testid="stSidebar"] {
        background: #111A2E;
        border-right: 1px solid #34415B;
    }

    [data-testid="stSidebar"] * {
        color: #F1F5F9;
    }

    .main .block-container {
        max-width: 1450px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    h1, h2, h3, h4 {
        color: #FFFFFF !important;
        font-weight: 750 !important;
    }

    p, li, label, .stMarkdown {
        color: #E0E7F1;
        line-height: 1.75;
    }

    [data-testid="stCaptionContainer"] {
        color: #B8C6DC !important;
    }

    .hero {
        padding: 32px;
        border: 1px solid #3B4E77;
        border-radius: 18px;
        background: linear-gradient(
            125deg,
            #172554,
            #17213A,
            #172033
        );
        margin-bottom: 25px;
    }

    .hero-kicker {
        font-size: 12px;
        color: #BFDBFE;
        font-weight: 800;
        letter-spacing: 2px;
    }

    .hero-title {
        font-size: 36px;
        font-weight: 800;
        line-height: 1.3;
        color: #FFFFFF;
        margin-top: 12px;
    }

    .hero-text {
        color: #E0E9F8;
        font-size: 15px;
        line-height: 1.9;
        margin-top: 12px;
    }

    .card {
        background: #141E32;
        border: 1px solid #34415B;
        border-radius: 14px;
        padding: 21px;
        min-height: 155px;
        margin-bottom: 12px;
    }

    .card-title {
        color: #FFFFFF;
        font-size: 17px;
        font-weight: 750;
        margin-bottom: 10px;
    }

    .card-text {
        color: #D0DAE9;
        font-size: 14px;
        line-height: 1.85;
    }

    .metric {
        background: #141E32;
        border: 1px solid #34415B;
        border-radius: 13px;
        padding: 18px;
        min-height: 115px;
    }

    .metric-label {
        color: #C3D0E3;
        font-size: 13px;
        font-weight: 600;
    }

    .metric-value {
        color: #FFFFFF;
        font-size: 26px;
        font-weight: 800;
        margin-top: 10px;
        overflow-wrap: anywhere;
    }

    .metric-help {
        color: #B4C3D9;
        font-size: 12px;
        margin-top: 8px;
        line-height: 1.6;
    }

    .notice {
        padding: 16px;
        border: 1px solid #82672C;
        background: #332A19;
        border-radius: 12px;
        color: #FDE7A1;
        line-height: 1.8;
        margin: 16px 0;
    }

    .success-box {
        padding: 16px;
        border: 1px solid #28765F;
        background: #14332D;
        border-radius: 12px;
        color: #B7F7DA;
        line-height: 1.8;
        margin: 16px 0;
    }

    .stButton > button,
    .stDownloadButton > button {
        min-height: 44px;
        border-radius: 9px;
        font-weight: 700;
        border: 1px solid #52668E;
    }

    .stButton > button[kind="primary"] {
        background: #315BEA;
        color: #FFFFFF;
    }

    .stButton > button:hover {
        border-color: #BFDBFE;
        color: #FFFFFF;
    }

    [data-baseweb="select"] > div {
        background: #172238;
        color: #FFFFFF;
        border-color: #435371;
    }

    .stTextInput input,
    .stNumberInput input {
        color: #FFFFFF;
        background: #172238;
    }

    [data-testid="stDataFrame"] {
        border: 1px solid #34415B;
        border-radius: 10px;
    }

    hr {
        border-color: #34415B;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ==========================================================
# HELPER FUNCTIONS
# ==========================================================

def metric_card(label, value, description):
    st.markdown(
        f"""
        <div class="metric">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-help">{description}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def go_to(page):
    st.session_state.page = page


def show_chart(fig):
    fig.update_layout(
        paper_bgcolor="#141E32",
        plot_bgcolor="#141E32",
        font=dict(
            color="#E0E7F1",
            family="Inter",
            size=13,
        ),
        title_font=dict(
            color="#FFFFFF",
            size=18,
        ),
        xaxis=dict(
            gridcolor="#34415B",
            zerolinecolor="#34415B",
        ),
        yaxis=dict(
            gridcolor="#34415B",
            zerolinecolor="#34415B",
        ),
        margin=dict(l=25, r=25, t=65, b=35),
    )

    st.plotly_chart(fig, use_container_width=True)


def export_csv(df):
    return df.to_csv(index=False).encode("utf-8")


# ==========================================================
# SIDEBAR NAVIGATION
# ==========================================================

with st.sidebar:

    st.markdown(
        """
        <div style="padding: 12px 0 20px 0;">
            <div style="font-size: 35px;">🛡️</div>
            <div style="
                font-size: 24px;
                font-weight: 800;
                color: #FFFFFF;
            ">
                Privacy Guard AI
            </div>
            <div style="
                color: #BFDBFE;
                font-size: 12px;
                letter-spacing: 1px;
            ">
                PRIVACY RESEARCH PLATFORM
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.markdown("### NAVIGATION")

    navigation = [
        ("Dashboard", "🏠"),
        ("Upload Dataset", "📁"),
        ("Anonymize Data", "🔐"),
        ("Performance Matrix", "📊"),
        ("Validation Results", "🔎"),
        ("Experiment History", "📚"),
        ("About Project", "ℹ️"),
    ]

    for name, icon in navigation:

        if st.button(
            f"{icon}  {name}",
            key=f"navigation_{name}",
            use_container_width=True,
            type=(
                "primary"
                if st.session_state.page == name
                else "secondary"
            ),
        ):
            go_to(name)
            st.rerun()

    st.markdown("---")

    st.markdown("### APPLICATION STATUS")

    st.markdown(
        """
        <div class="success-box">
            <b>Frontend:</b> Streamlit<br>
            <b>Backend:</b> Python<br>
            <b>Processing:</b> Local execution<br>
            <b>Input:</b> CSV / Excel
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.caption("Research prototype · Synthetic testing recommended")


# ==========================================================
# PAGE HEADER
# ==========================================================

page = st.session_state.page

st.markdown(
    f"""
    <div style="
        font-size: 12px;
        color: #93C5FD;
        font-weight: 800;
        letter-spacing: 2px;
    ">
        PRIVACY • ANONYMIZATION • PERFORMANCE
    </div>

    <div style="
        font-size: 32px;
        color: #FFFFFF;
        font-weight: 800;
        margin-top: 8px;
    ">
        {page}
    </div>

    <div style="
        color: #C3D0E3;
        font-size: 14px;
        margin-top: 8px;
        margin-bottom: 24px;
        line-height: 1.8;
    ">
        Detect private information, protect your dataset,
        and analyze multi-agent processing performance.
    </div>
    """,
    unsafe_allow_html=True,
)


# ==========================================================
# DASHBOARD
# ==========================================================

if page == "Dashboard":

    st.markdown(
        """
        <div class="hero">
            <div class="hero-kicker">
                AI • DATA PRIVACY • MULTI-AGENT SYSTEMS
            </div>

            <div class="hero-title">
                Protect Data.<br>
                Measure Performance.
            </div>

            <div class="hero-text">
                Privacy Guard AI is an interactive research prototype
                that detects common private-data patterns, anonymizes
                selected fields, validates the output, and evaluates
                the performance of its processing agents.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    result = st.session_state.result
    history = st.session_state.history

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        metric_card(
            "Dataset",
            "Loaded" if st.session_state.source_df is not None else "Not loaded",
            "Upload a CSV or Excel file",
        )

    with c2:
        metric_card(
            "Rows",
            f'{len(st.session_state.source_df):,}'
            if st.session_state.source_df is not None
            else "—",
            "Records in the current dataset",
        )

    with c3:
        metric_card(
            "Experiments",
            str(len(history)),
            "Runs recorded in this session",
        )

    with c4:
        metric_card(
            "Latest processing time",
            f'{result["total_ms"]:.2f} ms'
            if result is not None
            else "—",
            "Compute plus modeled coordination",
        )

    st.markdown("## Explore the platform")

    col1, col2 = st.columns(2)

    with col1:

        st.markdown(
            """
            <div class="card">
                <div class="card-title">📁 Upload Dataset</div>
                <div class="card-text">
                    Select a CSV or Excel file. Preview the data,
                    inspect its structure, and identify columns
                    that may contain private information.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button(
            "Open Dataset Upload →",
            key="dashboard_upload",
            use_container_width=True,
        ):
            go_to("Upload Dataset")
            st.rerun()

    with col2:

        st.markdown(
            """
            <div class="card">
                <div class="card-title">🔐 Anonymize Data</div>
                <div class="card-text">
                    Select sensitive fields, execute the
                    anonymization pipeline, inspect protected
                    records, and download the output.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button(
            "Open Anonymization →",
            key="dashboard_anonymize",
            use_container_width=True,
        ):
            go_to("Anonymize Data")
            st.rerun()

    col3, col4 = st.columns(2)

    with col3:

        st.markdown(
            """
            <div class="card">
                <div class="card-title">📊 Performance Matrix</div>
                <div class="card-text">
                    Compare agent execution times, throughput,
                    coordination cost, and overall processing time.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button(
            "Open Performance Matrix →",
            key="dashboard_performance",
            use_container_width=True,
        ):
            go_to("Performance Matrix")
            st.rerun()

    with col4:

        st.markdown(
            """
            <div class="card">
                <div class="card-title">🔎 Validation Results</div>
                <div class="card-text">
                    Review the detectable private-data patterns
                    remaining after anonymization and understand
                    the limitations of automated detection.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button(
            "Open Validation →",
            key="dashboard_validation",
            use_container_width=True,
        ):
            go_to("Validation Results")
            st.rerun()

    st.markdown("---")

    st.markdown("## Processing architecture")

    architecture = pd.DataFrame([
        {
            "Stage": "Agent 1",
            "Component": "Detection Agent",
            "Purpose": "Identify potentially sensitive information",
        },
        {
            "Stage": "Agent 2",
            "Component": "Anonymization Agent",
            "Purpose": "Mask selected fields and text patterns",
        },
        {
            "Stage": "Agent 3",
            "Component": "Validation Agent",
            "Purpose": "Check for remaining detectable patterns",
        },
    ])

    st.dataframe(
        architecture,
        use_container_width=True,
        hide_index=True,
    )

    st.markdown(
        """
        <div class="notice">
            <b>Research limitation:</b> The current agents execute
            sequentially in one Python process. Coordination
            overhead is modeled, not measured over a real network.
            Anonymization and validation do not guarantee complete
            privacy or security.
        </div>
        """,
        unsafe_allow_html=True,
    )


# ==========================================================
# UPLOAD DATASET
# ==========================================================

elif page == "Upload Dataset":

    st.markdown("## Upload your dataset")

    st.write(
        "Supported formats: CSV, XLSX, and XLS. "
        "Use synthetic or appropriately authorized data while testing."
    )

    uploaded_file = st.file_uploader(
        "Choose a dataset",
        type=["csv", "xlsx", "xls"],
        key="dataset_uploader",
    )

    if uploaded_file is not None:

        try:

            # Read the file only after the user uploads it.
            df = load_dataset(
                uploaded_file.getvalue(),
                uploaded_file.name,
            )

            st.session_state.source_df = df
            st.session_state.filename = uploaded_file.name

            st.markdown(
                """
                <div class="success-box">
                    Dataset loaded successfully.
                </div>
                """,
                unsafe_allow_html=True,
            )

            c1, c2, c3 = st.columns(3)

            with c1:
                metric_card(
                    "Rows",
                    f"{len(df):,}",
                    "Number of records",
                )

            with c2:
                metric_card(
                    "Columns",
                    str(len(df.columns)),
                    "Number of fields",
                )

            with c3:
                metric_card(
                    "Missing cells",
                    f"{int(df.isna().sum().sum()):,}",
                    "Empty or missing values",
                )

            st.markdown("### Dataset preview")

            st.dataframe(
                df.head(20),
                use_container_width=True,
                hide_index=True,
            )

            st.markdown("### Column information")

            schema = pd.DataFrame({
                "Column": df.columns.astype(str),
                "Data type": [
                    str(dtype) for dtype in df.dtypes
                ],
                "Missing values": [
                    int(df[col].isna().sum())
                    for col in df.columns
                ],
            })

            st.dataframe(
                schema,
                use_container_width=True,
                hide_index=True,
            )

            if st.button(
                "Continue to Anonymization →",
                type="primary",
                use_container_width=True,
            ):
                go_to("Anonymize Data")
                st.rerun()

        except Exception as error:
            st.error(f"Unable to load the dataset: {error}")

    elif st.session_state.source_df is not None:

        st.info(
            f"Previously loaded dataset: "
            f"{st.session_state.filename}"
        )

        if st.button("Open Existing Dataset"):

            st.dataframe(
                st.session_state.source_df.head(20),
                use_container_width=True,
                hide_index=True,
            )


# ==========================================================
# ANONYMIZE DATA
# ==========================================================

elif page == "Anonymize Data":

    df = st.session_state.source_df

    if df is None:

        st.warning(
            "Please upload a dataset before starting anonymization."
        )

        if st.button(
            "Go to Dataset Upload →",
            type="primary",
        ):
            go_to("Upload Dataset")
            st.rerun()

    else:

        st.markdown("## Configure anonymization")

        st.write(
            "The application detects potentially sensitive columns "
            "from their names. You can review and change the selection "
            "before executing the pipeline."
        )

        detected = {}

        # Preview detection without anonymizing the original data.
        from backend import detect_sensitive_columns

        detected = detect_sensitive_columns(df)

        suggested = sorted({
            col
            for cols in detected.values()
            for col in cols
        })

        st.markdown("### Suggested sensitive columns")

        if suggested:

            st.dataframe(
                pd.DataFrame({
                    "Suggested sensitive column": suggested
                }),
                use_container_width=True,
                hide_index=True,
            )

        else:

            st.info(
                "No sensitive column names were detected. "
                "Review the dataset carefully before proceeding."
            )

        selected_columns = st.multiselect(
            "Select columns to anonymize",
            options=list(df.columns),
            default=suggested,
            help=(
                "Selected columns are replaced with stable "
                "SHA-256-derived tokens. Other columns are scanned "
                "for common email, phone, ID, and IP patterns."
            ),
        )

        st.markdown("### Multi-agent configuration")

        col1, col2 = st.columns(2)

        with col1:

            agent_count = st.slider(
                "Number of agents",
                min_value=3,
                max_value=10,
                value=3,
                help=(
                    "The first three agents perform the processing "
                    "stages. Additional agents affect modeled "
                    "coordination cost only."
                ),
            )

        with col2:

            coordination_cost = st.number_input(
                "Assumed cost per coordination message (ms)",
                min_value=0.0,
                max_value=1000.0,
                value=0.1,
                step=0.1,
                help=(
                    "This is a simulation parameter, not a "
                    "measurement of real network latency."
                ),
            )

        st.markdown(
            """
            <div class="notice">
                <b>Before proceeding:</b> This prototype modifies
                a working copy of the uploaded dataset. It does not
                change the original file on your computer. Do not
                upload confidential datasets to a public deployment
                unless the deployment and its data handling have
                been appropriately reviewed.
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button(
            "🔐 Run Anonymization Pipeline",
            type="primary",
            use_container_width=True,
        ):

            try:

                with st.spinner(
                    "Detection, anonymization, and validation agents "
                    "are processing the dataset..."
                ):

                    result = run_privacy_pipeline(
                        df=df,
                        selected_columns=selected_columns,
                        agent_count=agent_count,
                        coordination_cost_ms=coordination_cost,
                    )

                st.session_state.result = result

                st.session_state.history.append({
                    "Experiment": len(st.session_state.history) + 1,
                    "Time": datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    "Filename": st.session_state.filename,
                    "Rows": len(df),
                    "Agents": agent_count,
                    "Columns Masked": len(selected_columns),
                    "Changed Cells": result["changed_cells"],
                    "Compute Time (ms)": round(
                        result["measured_compute_ms"], 3
                    ),
                    "Coordination (ms)": round(
                        result["coordination_ms"], 3
                    ),
                    "Total Time (ms)": round(
                        result["total_ms"], 3
                    ),
                })

                st.success(
                    "Anonymization pipeline completed successfully."
                )

                go_to("Validation Results")
                st.rerun()

            except Exception as error:

                st.error(
                    f"Anonymization failed: {error}"
                )

        result = st.session_state.result

        if result is not None:

            st.markdown("---")
            st.markdown("## Protected dataset")

            st.dataframe(
                result["protected_df"].head(20),
                use_container_width=True,
                hide_index=True,
            )

            csv_bytes = export_csv(
                result["protected_df"]
            )

            st.download_button(
                "⬇ Download Anonymized CSV",
                data=csv_bytes,
                file_name="privacy_guard_anonymized.csv",
                mime="text/csv",
                use_container_width=True,
            )

            st.info(
                "The download contains the protected data. "
                "Review the validation results before using it."
            )


# ==========================================================
# PERFORMANCE MATRIX
# ==========================================================

elif page == "Performance Matrix":

    result = st.session_state.result

    if result is None:

        st.warning(
            "No performance measurements are available yet. "
            "Upload a dataset and run the anonymization pipeline."
        )

        if st.button(
            "Start Experiment →",
            type="primary",
        ):
            go_to("Anonymize Data")
            st.rerun()

    else:

        st.markdown("## Overall performance")

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            metric_card(
                "Records processed",
                f'{result["row_count"]:,}',
                "Rows in the dataset",
            )

        with c2:
            metric_card(
                "Compute time",
                f'{result["measured_compute_ms"]:.2f} ms',
                "Measured local processing time",
            )

        with c3:
            metric_card(
                "Coordination cost",
                f'{result["coordination_ms"]:.2f} ms',
                "Modeled, not network-measured",
            )

        with c4:
            metric_card(
                "Throughput",
                f'{result["throughput"]:.2f}',
                "Records per second, including modeled cost",
            )

        st.markdown("### Agent performance matrix")

        matrix = result["performance_matrix"]

        st.dataframe(
            matrix,
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("### Execution time by agent")

        fig = px.bar(
            matrix,
            x="Agent",
            y="Execution Time (ms)",
            color="Agent",
            text="Execution Time (ms)",
            title="Measured local processing time",
            color_discrete_sequence=[
                "#60A5FA",
                "#A78BFA",
                "#34D399",
            ],
        )

        fig.update_traces(
            texttemplate="%{text:.3f}",
            textposition="outside",
        )

        show_chart(fig)

        st.markdown("### Processing time breakdown")

        breakdown = pd.DataFrame({
            "Stage": [
                "Detection",
                "Anonymization",
                "Validation",
                "Modeled coordination",
            ],
            "Time (ms)": [
                result["detection_ms"],
                result["anonymization_ms"],
                result["validation_ms"],
                result["coordination_ms"],
            ],
        })

        fig2 = px.pie(
            breakdown,
            names="Stage",
            values="Time (ms)",
            hole=0.55,
            title="Distribution of measured and modeled time",
            color_discrete_sequence=[
                "#60A5FA",
                "#A78BFA",
                "#34D399",
                "#FBBF24",
            ],
        )

        show_chart(fig2)

        st.markdown("### Performance definitions")

        st.markdown(
            """
            **Execution time:** Time spent in a processing stage.

            **Throughput:** Number of records divided by elapsed time.

            **Coordination cost:** Assumed cost per modeled message
            multiplied by the modeled message count.

            **Total time:** Measured processing time plus modeled
            coordination cost.
            """
        )

        st.markdown(
            """
            <div class="notice">
                The additional agent count does not create more
                processing workers in this version. The system
                measures three sequential processing stages and
                estimates coordination cost separately. Therefore,
                these results should not be presented as measured
                performance of a distributed multi-agent system.
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.download_button(
            "⬇ Download Performance Matrix",
            data=export_csv(matrix),
            file_name="privacy_guard_performance.csv",
            mime="text/csv",
            use_container_width=True,
        )


# ==========================================================
# VALIDATION RESULTS
# ==========================================================

elif page == "Validation Results":

    result = st.session_state.result

    if result is None:

        st.warning(
            "Run the anonymization pipeline to generate validation results."
        )

        if st.button(
            "Go to Anonymization →",
            type="primary",
        ):
            go_to("Anonymize Data")
            st.rerun()

    else:

        validation = result["validation"]

        st.markdown("## Privacy validation report")

        if validation["total_remaining_patterns"] == 0:

            st.success(
                "No tested patterns were detected in the scanned columns."
            )

        else:

            st.warning(
                "Some detectable private-data patterns remain. "
                "Inspect the findings below."
            )

        c1, c2, c3 = st.columns(3)

        with c1:
            metric_card(
                "Changed cells",
                f'{result["changed_cells"]:,}',
                "Cells modified during anonymization",
            )

        with c2:
            metric_card(
                "Remaining pattern matches",
                f'{validation["total_remaining_patterns"]:,}',
                "Matches from the tested pattern rules",
            )

        with c3:
            metric_card(
                "Columns scanned",
                str(validation["columns_checked"]),
                "Columns checked after masking",
            )

        st.markdown("### Detected before anonymization")

        before_df = pd.DataFrame({
            "Pattern type": list(
                result["before_patterns"].keys()
            ),
            "Matches before": list(
                result["before_patterns"].values()
            ),
        })

        st.dataframe(
            before_df,
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("### Patterns remaining after anonymization")

        after_counts = validation["remaining_pattern_counts"]

        after_df = pd.DataFrame({
            "Pattern type": list(after_counts.keys()),
            "Matches remaining": list(after_counts.values()),
        })

        st.dataframe(
            after_df,
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("### Validation interpretation")

        st.markdown(
            """
            - Zero matches means only that the configured pattern
              rules found no matches in the scanned columns.
            - A remaining match indicates a possible item requiring
              further review; it is not necessarily a private value.
            - The rules may miss names, unusual phone formats,
              free-text identifiers, and indirect identifiers.
            - Validation is not a proof of anonymity or security.
            """
        )

        st.markdown(
            """
            <div class="notice">
                If you need stronger privacy protection, consider
                adding context-aware entity recognition, a defined
                threat model, re-identification tests, and
                differential privacy where appropriate.
            </div>
            """,
            unsafe_allow_html=True,
        )


# ==========================================================
# EXPERIMENT HISTORY
# ==========================================================

elif page == "Experiment History":

    st.markdown("## Previous experiment runs")

    history = st.session_state.history

    if history:

        history_df = pd.DataFrame(history)

        st.dataframe(
            history_df,
            use_container_width=True,
            hide_index=True,
        )

        if "Total Time (ms)" in history_df.columns:

            fig = px.bar(
                history_df,
                x="Experiment",
                y="Total Time (ms)",
                title="Total processing time by experiment",
                color_discrete_sequence=["#60A5FA"],
            )

            show_chart(fig)

        st.download_button(
            "⬇ Download Experiment History",
            data=export_csv(history_df),
            file_name="privacy_guard_history.csv",
            mime="text/csv",
            use_container_width=True,
        )

        if st.button("Clear History"):

            st.session_state.history = []
            st.rerun()

    else:

        st.info(
            "No experiments have been recorded in this session yet."
        )

        if st.button(
            "Start Your First Experiment →",
            type="primary",
        ):
            go_to("Upload Dataset")
            st.rerun()


# ==========================================================
# ABOUT PROJECT
# ==========================================================

elif page == "About Project":

    st.markdown(
        """
        <div class="hero">
            <div class="hero-kicker">
                RESEARCH PROJECT
            </div>

            <div class="hero-title">
                Privacy Guard AI
            </div>

            <div class="hero-text">
                An interactive prototype for anonymizing datasets
                and analyzing processing performance and modeled
                coordination overhead in a multi-agent workflow.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("## Problem statement")

    st.write(
        "Datasets can contain sensitive personal information. "
        "Automated anonymization can help reduce direct exposure, "
        "but it also introduces processing costs and may fail to "
        "detect some private information. Privacy Guard AI provides "
        "a prototype for exploring these issues."
    )

    st.markdown("## Project objectives")

    objectives = [
        "Accept CSV and Excel datasets.",
        "Identify columns that appear to contain sensitive information.",
        "Mask selected columns and common private-data patterns.",
        "Validate output against configured detection rules.",
        "Measure execution time and throughput for each stage.",
        "Estimate coordination cost under explicit assumptions.",
        "Export protected data and performance reports.",
    ]

    for objective in objectives:
        st.markdown(f"- {objective}")

    st.markdown("## Technology stack")

    tech = pd.DataFrame([
        {
            "Technology": "Python",
            "Purpose": "Backend logic and data processing",
        },
        {
            "Technology": "Pandas",
            "Purpose": "Dataset manipulation",
        },
        {
            "Technology": "Streamlit",
            "Purpose": "Interactive frontend",
        },
        {
            "Technology": "Plotly",
            "Purpose": "Performance visualization",
        },
        {
            "Technology": "Git and GitHub",
            "Purpose": "Version control and project hosting",
        },
    ])

    st.dataframe(
        tech,
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("## Limitations and future development")

    st.markdown(
        """
        1. Implement real message passing between separate agents.
        2. Measure actual communication latency and message sizes.
        3. Add context-aware private-entity recognition.
        4. Evaluate privacy leakage using a defined threat model.
        5. Add differential privacy with an explicit privacy budget.
        6. Run repeated experiments and compare statistical results.
        7. Store experiment history persistently.
        """
    )

    st.markdown(
        """
        <div class="notice">
            This is a research prototype, not a production
            data-security product. Use appropriately authorized
            test data and review anonymization results before
            sharing or publishing any dataset.
        </div>
        """,
        unsafe_allow_html=True,
    )


# ==========================================================
# FOOTER
# ==========================================================

st.markdown("---")

st.markdown(
    """
    <div style="
        text-align: center;
        color: #B4C3D9;
        font-size: 12px;
        padding: 18px;
        line-height: 1.9;
    ">
        <b>Privacy Guard AI</b><br>
        Dataset Anonymization and Multi-Agent Performance Analysis<br>
        Python · Streamlit · Pandas · Plotly
    </div>
    """,
    unsafe_allow_html=True,
)
