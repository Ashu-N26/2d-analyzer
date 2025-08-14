import streamlit as st
import numpy as np
import plotly.graph_objects as go
import time
from utils import generate_approach_profile

st.set_page_config(page_title="IAC 2D Visual Analyzer", layout="wide")

st.title("🛬 IAC 2D Visual Analyzer")
st.markdown("Visualize aircraft flying an instrument approach in 2D.")

# Sidebar Inputs
st.sidebar.header("Approach Details")
runway = st.sidebar.text_input("Runway", "09")
faf_distance = st.sidebar.number_input("FAF to Threshold (NM)", 5.0, 20.0, 6.0, step=0.1)
faf_altitude = st.sidebar.number_input("FAF Altitude (ft)", 1000, 8000, 3000)
threshold_altitude = st.sidebar.number_input("Threshold Elevation (ft)", 0, 2000, 200)
mda = st.sidebar.number_input("MDA/DA (ft)", 0, 8000, 520)
ground_speed = st.sidebar.number_input("Ground Speed (kt)", 60, 250, 120)

sdf_points = st.sidebar.text_area("Step-Down Fixes (NM, Altitude ft)",
                                  "4.0, 2200\n3.0, 1800")

if st.sidebar.button("Run Simulation"):
    sdf_data = []
    for line in sdf_points.strip().split("\n"):
        try:
            nm, alt = line.split(",")
            sdf_data.append((float(nm), float(alt)))
        except:
            pass

    # Generate approach profile
    distances, alts = generate_approach_profile(
        faf_distance, faf_altitude, threshold_altitude, sdf_data
    )

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=distances, y=alts, mode="lines", name="Glide Path", line=dict(color="blue", width=2)))
    fig.add_hline(y=mda, line_dash="dash", line_color="red", annotation_text="MDA/DA", annotation_position="top left")

    # Animate Aircraft
    aircraft_marker = go.Scatter(
        x=[distances[0]], y=[alts[0]], mode="markers", marker=dict(size=12, color="orange"), name="Aircraft"
    )
    fig.add_trace(aircraft_marker)

    fig.update_layout(
        xaxis_title="Distance to Threshold (NM)",
        yaxis_title="Altitude (ft)",
        yaxis=dict(autorange="reversed"),  # invert altitude axis visually
        title=f"Approach Profile - RWY {runway}",
        height=500
    )

    chart_placeholder = st.empty()

    # Animation loop
    for i in range(len(distances)):
        aircraft_marker = go.Scatter(
            x=[distances[i]], y=[alts[i]], mode="markers", marker=dict(size=12, color="orange"), name="Aircraft"
        )
        frame_fig = go.Figure(data=[
            go.Scatter(x=distances, y=alts, mode="lines", name="Glide Path", line=dict(color="blue", width=2)),
            go.Scatter(x=[distances[i]], y=[alts[i]], mode="markers", marker=dict(size=12, color="orange"), name="Aircraft")
        ])
        frame_fig.add_hline(y=mda, line_dash="dash", line_color="red", annotation_text="MDA/DA", annotation_position="top left")
        frame_fig.update_layout(
            xaxis_title="Distance to Threshold (NM)",
            yaxis_title="Altitude (ft)",
            yaxis=dict(autorange="reversed"),
            title=f"Approach Profile - RWY {runway}",
            height=500
        )
        chart_placeholder.plotly_chart(frame_fig, use_container_width=True)
        time.sleep(0.3)
