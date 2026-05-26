import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from scipy.stats import norm
import datetime

st.set_page_config(page_title="Workstation Efficiency + Six Sigma Dashboard", layout="wide")

st.title("Workstation Efficiency Calculator")

# -----------------------
# SESSION STATE
# -----------------------
if "history" not in st.session_state:
    st.session_state.history = pd.DataFrame()

# -----------------------
# SIDEBAR INPUTS (ALL HOURS)
# -----------------------
st.sidebar.header("Input Parameters (All Time in Hours)")

workstation = st.sidebar.text_input("Workstation Name", "WS-1")

available_time = st.sidebar.number_input("Available Time (hours)", min_value=0.1, value=8.0)
downtime = st.sidebar.number_input("Downtime (hours)", min_value=0.0, value=1.0)
setup_time = st.sidebar.number_input("Setup Time (hours)", min_value=0.0, value=0.5)
cycle_time = st.sidebar.number_input("Ideal Cycle Time per Unit (hours)", min_value=0.0001, value=0.033)
actual_output = st.sidebar.number_input("Total Units Produced", min_value=0, value=180)
rejected_units = st.sidebar.number_input("Rejected Units", min_value=0, value=10)
operators = st.sidebar.number_input("Number of Operators", min_value=1, value=2)

# -----------------------
# VALIDATION
# -----------------------
if downtime + setup_time > available_time:
    st.error("Downtime + Setup Time cannot exceed Available Time")
    st.stop()

# -----------------------
# CALCULATIONS
# -----------------------
operating_time = available_time - downtime - setup_time
good_units = actual_output - rejected_units

productivity = actual_output / available_time
utilization = (operating_time / available_time) * 100

availability = operating_time / available_time
performance = (cycle_time * actual_output) / operating_time if operating_time > 0 else 0
quality = good_units / actual_output if actual_output > 0 else 0

oee = availability * performance * quality * 100
efficiency = (actual_output / (available_time / cycle_time)) * 100 if cycle_time > 0 else 0

# -----------------------
# SIX SIGMA ANALYTICS
# -----------------------
defect_rate = rejected_units / actual_output if actual_output > 0 else 0
yield_percent = (good_units / actual_output) * 100 if actual_output > 0 else 0
dpmo = defect_rate * 1_000_000

# Sigma level approximation (with 1.5 sigma shift)
if defect_rate > 0 and defect_rate < 1:
    sigma_level = norm.ppf(1 - defect_rate) + 1.5
else:
    sigma_level = 0

# -----------------------
# KPI DISPLAY
# -----------------------
col1, col2, col3, col4 = st.columns(4)
col1.metric("Efficiency %", f"{efficiency:.2f}%")
col2.metric("Utilization %", f"{utilization:.2f}%")
col3.metric("OEE %", f"{oee:.2f}%")
col4.metric("Productivity (units/hr)", f"{productivity:.2f}")

# -----------------------
# OEE GAUGE
# -----------------------
gauge = go.Figure(go.Indicator(
    mode="gauge+number",
    value=oee,
    title={'text': "OEE %"},
    gauge={
        'axis': {'range': [0, 100]},
        'steps': [
            {'range': [0, 70], 'color': "red"},
            {'range': [70, 85], 'color': "yellow"},
            {'range': [85, 100], 'color': "green"}
        ]
    }
))
st.plotly_chart(gauge, use_container_width=True)

# -----------------------
# TIME LOSS PIE
# -----------------------
loss_data = pd.DataFrame({
    "Category": ["Downtime", "Setup", "Operating"],
    "Hours": [downtime, setup_time, operating_time]
})
st.plotly_chart(px.pie(loss_data, names="Category", values="Hours", title="Time Breakdown"),
                use_container_width=True)

# -----------------------
# SIX SIGMA DISPLAY
# -----------------------
st.subheader("Six Sigma Analytics")

s1, s2, s3, s4 = st.columns(4)
s1.metric("Defect %", f"{defect_rate*100:.2f}%")
s2.metric("Yield %", f"{yield_percent:.2f}%")
s3.metric("DPMO", f"{dpmo:,.0f}")
s4.metric("Sigma Level", f"{sigma_level:.2f}")

# -----------------------
# SIGMA INTERPRETATION
# -----------------------
if sigma_level < 3:
    st.error("Process is below 3 Sigma (High Defects). Immediate improvement needed.")
elif sigma_level < 4:
    st.warning("Process between 3–4 Sigma. Moderate quality level.")
elif sigma_level < 5:
    st.info("Process between 4–5 Sigma. Good quality performance.")
else:
    st.success("Excellent! Near Six Sigma quality.")

# -----------------------
# IMPROVEMENT SUGGESTIONS
# -----------------------
st.subheader("Improvement Suggestions")

if availability < 0.85:
    st.warning("Reduce downtime and improve preventive maintenance.")

if performance < 0.90:
    st.warning("Optimize cycle time and eliminate micro-stoppages.")

if quality < 0.95:
    st.warning("Reduce defects through root cause analysis.")

if sigma_level < 4:
    st.warning("Apply DMAIC methodology to improve process stability.")

# -----------------------
# SAVE HISTORY
# -----------------------
if st.button("Save to History"):
    new_row = pd.DataFrame([{
        "Timestamp": datetime.datetime.now(),
        "Workstation": workstation,
        "OEE %": oee,
        "Sigma Level": sigma_level
    }])
    st.session_state.history = pd.concat([st.session_state.history, new_row], ignore_index=True)
    st.success("Saved Successfully!")

# -----------------------
# HISTORY TREND
# -----------------------
if not st.session_state.history.empty:
    st.subheader("Historical Trend")
    st.dataframe(st.session_state.history)

    st.plotly_chart(px.line(st.session_state.history,
                            x="Timestamp",
                            y="Sigma Level",
                            color="Workstation",
                            title="Sigma Level Trend"),
                    use_container_width=True)
