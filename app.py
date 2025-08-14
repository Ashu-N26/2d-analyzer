import streamlit as st
import plotly.graph_objects as go
import time

st.set_page_config(page_title="2D Aircraft Path Analyzer", layout="wide")

st.title("✈️ 2D Aircraft Path Analyzer & Visualizer")

# Sidebar inputs
st.sidebar.header("Simulation Settings")
num_frames = st.sidebar.slider("Number of Frames", 5, 100, 20)
frame_delay = st.sidebar.slider("Frame Delay (seconds)", 0.05, 1.0, 0.2)

st.sidebar.header("Aircraft Path Parameters")
start_alt = st.sidebar.number_input("Starting Altitude (ft)", 0, 50000, 5000)
end_alt = st.sidebar.number_input("Ending Altitude (ft)", 0, 50000, 0)
distance_nm = st.sidebar.number_input("Total Distance (NM)", 1, 500, 50)

# Generate simulation frames
altitudes = []
distances = []
for i in range(num_frames):
    fraction = i / (num_frames - 1)
    altitude = start_alt + fraction * (end_alt - start_alt)
    distance = fraction * distance_nm
    altitudes.append(altitude)
    distances.append(distance)

simulation_frames = [{"x": distances[:i+1], "y": altitudes[:i+1]} for i in range(num_frames)]

chart_placeholder = st.empty()

# Simulate animation
for frame_idx, frame_data in enumerate(simulation_frames):
    frame_fig = go.Figure()

    frame_fig.add_trace(go.Scatter(
        x=frame_data["x"],  # X-axis: distance
        y=frame_data["y"],  # Y-axis: altitude
        mode='lines+markers',
        line=dict(color='blue'),
        marker=dict(size=6),
        name="Aircraft Path"
    ))

    # Ensure altitude is displayed correctly (upward positive)
    frame_fig.update_yaxes(autorange=True)

    frame_fig.update_layout(
        title=f"Aircraft Simulation Frame {frame_idx+1}/{num_frames}",
        xaxis_title="Distance (NM)",
        yaxis_title="Altitude (ft)",
        template="plotly_dark"
    )

    chart_placeholder.plotly_chart(frame_fig, use_container_width=True, key=f"frame_{frame_idx}")

    time.sleep(frame_delay)

st.success("Simulation complete ✅")

