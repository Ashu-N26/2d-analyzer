
import os
import math
import time
import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go
import requests
import srtm

st.set_page_config(page_title="IAC 2D Analyzer — Terrain & Obstacles", layout="wide")

# ---------- Utilities ----------
def meters_to_feet(m):
    return None if m is None else m / 0.3048

def destination_point(lat_deg, lon_deg, bearing_deg, distance_km):
    lat1 = math.radians(lat_deg); lon1 = math.radians(lon_deg); br = math.radians(bearing_deg)
    R = 6371.0
    d_R = distance_km / R
    lat2 = math.asin(math.sin(lat1)*math.cos(d_R) + math.cos(lat1)*math.sin(d_R)*math.cos(br))
    lon2 = lon1 + math.atan2(math.sin(br)*math.sin(d_R)*math.cos(lat1),
                             math.cos(d_R)-math.sin(lat1)*math.sin(lat2))
    return math.degrees(lat2), math.degrees(lon2)

def sample_approach_points(thr_lat, thr_lon, approach_bearing_deg, faf_to_thr_nm, samples):
    inv_bearing = (approach_bearing_deg + 180.0) % 360.0
    dists_nm = [faf_to_thr_nm * (1.0 - (i/(samples-1))) for i in range(samples)]
    coords = []
    for d in dists_nm:
        km = d * 1.852
        lat, lon = destination_point(thr_lat, thr_lon, inv_bearing, km)
        coords.append({"lat": lat, "lon": lon, "d_nm_from_thr": round(d, 6)})
    return coords

def get_elevations_srtm(coords):
    data = srtm.get_data()
    elevs = []
    for c in coords:
        try:
            e = data.get_elevation(c['lat'], c['lon'])
        except Exception:
            e = None
        elevs.append(e)
    return elevs

def get_elevations_open_elevation(coords):
    url = "https://api.open-elevation.com/api/v1/lookup"
    batch_size = 80
    elevations = []
    try:
        for i in range(0, len(coords), batch_size):
            batch = coords[i:i+batch_size]
            payload = {"locations": [{"latitude": c["lat"], "longitude": c["lon"]} for c in batch]}
            resp = requests.post(url, json=payload, timeout=30)
            if resp.status_code != 200:
                return None
            data = resp.json()
            for r in data.get("results", []):
                elevations.append(r.get("elevation", None))
        return elevations
    except Exception:
        return None

def get_elevations_google(coords):
    GOOGLE_API = os.environ.get("GOOGLE_API_KEY", "").strip()
    if not GOOGLE_API:
        return None
    url = "https://maps.googleapis.com/maps/api/elevation/json"
    elevations = []
    batch = []
    max_batch = 100
    for i, c in enumerate(coords):
        batch.append(f"{c['lat']},{c['lon']}")
        if len(batch) >= max_batch or i == len(coords)-1:
            params = {"locations": "|".join(batch), "key": GOOGLE_API}
            try:
                r = requests.get(url, params=params, timeout=30)
                j = r.json()
                if j.get("status") != "OK":
                    return None
                for res in j.get("results", []):
                    elevations.append(res.get("elevation"))
            except Exception:
                return None
            batch = []
    return elevations

def load_csv(path):
    try:
        return pd.read_csv(path, comment="#")
    except Exception as e:
        st.error(f"Failed to load {path}: {e}")
        return None

def find_runway(icao, rw_ident, airports_df, runways_df):
    if airports_df is None or runways_df is None:
        return None
    icao = icao.strip().upper(); rw_ident = rw_ident.strip().upper()
    rwy = runways_df[(runways_df['airport_ident'].str.upper() == icao) &
                     ((runways_df['le_ident'].str.upper() == rw_ident) | (runways_df['he_ident'].str.upper() == rw_ident))]
    if rwy.empty:
        # fall back to runway number only
        num = ''.join([c for c in rw_ident if c.isdigit()])
        if num:
            rwy = runways_df[runways_df['airport_ident'].str.upper() == icao]
            rwy = rwy[(rwy['le_ident'].str.startswith(num)) | (rwy['he_ident'].str.startswith(num))]
    if rwy.empty:
        return None
    row = rwy.iloc[0]
    # Which end matched?
    if str(row['le_ident']).upper() == rw_ident or (num and str(row['le_ident']).startswith(num)):
        thr_lat = float(row['le_latitude_deg']); thr_lon = float(row['le_longitude_deg'])
        bearing = float(row.get('le_heading_deg', 0.0))
        end = str(row['le_ident'])
    else:
        thr_lat = float(row['he_latitude_deg']); thr_lon = float(row['he_longitude_deg'])
        bearing = float(row.get('he_heading_deg', 0.0))
        end = str(row['he_ident'])
    return {"threshold_lat": thr_lat, "threshold_lon": thr_lon, "approach_bearing_deg": bearing, "runway_end": end}

# ---------- UI ----------
st.title("IAC 2D Visual Analyzer — Terrain & Obstacles (Pro)")

with st.sidebar:
    st.header("Data Sources")
    elev_source = st.selectbox("Elevation source", ["srtm (offline)", "open-elevation (web)", "google (web)"], index=0)
    st.caption("Set GOOGLE_API_KEY in environment to enable Google Elevation.")

    st.header("Airport / Approach")
    icao = st.text_input("ICAO", value="KSFO")
    rwy = st.text_input("Runway (e.g., 28R, 09L)", value="28R")
    airports_df = load_csv("airports.csv")
    runways_df = load_csv("runways.csv")

    auto_btn = st.button("Auto-fill from ICAO + Runway")

    # Manual fields (will be overridden by auto-fill if available)
    thr_lat = st.number_input("Threshold Latitude (deg)", format="%.6f", value=37.618805)
    thr_lon = st.number_input("Threshold Longitude (deg)", format="%.6f", value=-122.375416)
    approach_bearing = st.number_input("Approach Bearing (deg)", min_value=0.0, max_value=360.0, value=281.0, step=0.1)

    if auto_btn and icao and rwy:
        res = find_runway(icao, rwy, airports_df, runways_df)
        if res:
            thr_lat = res["threshold_lat"]; thr_lon = res["threshold_lon"]; approach_bearing = res["approach_bearing_deg"]
            st.success(f"Auto-filled from {icao} {res['runway_end']}: lat {thr_lat:.6f}, lon {thr_lon:.6f}, bearing {approach_bearing:.1f}°")
        else:
            st.error("Runway not found in database.")

    st.header("Approach Geometry")
    faf_to_thr_nm = st.number_input("FAF → Threshold (NM)", value=6.0, min_value=0.5, step=0.5)
    faf_alt_ft = st.number_input("FAF Altitude (ft MSL)", value=1800, step=10)
    mda_ft = st.number_input("MDA / DA (ft MSL)", value=720, step=10)
    safety_buffer_ft = st.number_input("Safety buffer over terrain (ft)", value=100, step=10)

    st.header("Step-down Fixes (Optional)")
    sdf_csv = st.file_uploader("Upload Step-down fixes CSV (dist_nm,alt_ft,label)", type=["csv"])

    st.header("Obstacles / Terrain (Optional)")
    obs_csv = st.file_uploader("Upload obstacles CSV (dist_nm,height_ft,label)", type=["csv"])
    st.caption("dist_nm measured from threshold along approach path.")

    st.header("DME Table (Optional)")
    dme_dist = st.number_input("DME distance (NM) to compute target altitude", value=5.0, step=0.1)

    st.header("Simulation")
    samples = st.slider("Samples (frames)", 50, 800, 240)
    frame_delay = st.slider("Frame delay (sec)", 0.0, 0.3, 0.02)

run_sim = st.button("Run Simulation")

if run_sim:
    with st.spinner("Computing approach profile & retrieving terrain..."):
        coords = sample_approach_points(thr_lat, thr_lon, approach_bearing, faf_to_thr_nm, samples)

        # elevation retrieval with fallback chain
        elevs_m = None
        if elev_source.startswith("google"):
            elevs_m = get_elevations_google(coords) or get_elevations_srtm(coords)
        elif elev_source.startswith("open-elevation"):
            elevs_m = get_elevations_open_elevation(coords) or get_elevations_srtm(coords)
        else:
            elevs_m = get_elevations_srtm(coords)

        for i, c in enumerate(coords):
            c["elev_m"] = elevs_m[i] if elevs_m and i < len(elevs_m) else None
            c["elev_ft"] = meters_to_feet(c["elev_m"]) if c["elev_m"] is not None else None

        # CDFA linear descent to MDA/DA
        alt_profile_ft = []
        dists = [c["d_nm_from_thr"] for c in coords]
        for c in coords:
            dist_from_thr = c["d_nm_from_thr"]
            dist_from_faf = faf_to_thr_nm - dist_from_thr
            dist_from_faf = max(0.0, min(faf_to_thr_nm, dist_from_faf))
            alt = faf_alt_ft - (faf_alt_ft - mda_ft) * (dist_from_faf / max(faf_to_thr_nm, 1e-6))
            alt_profile_ft.append(alt)

        # Step-down fixes overlay
        sdf_pts = []
        if sdf_csv is not None:
            try:
                sdf_df = pd.read_csv(sdf_csv)
                for _, r in sdf_df.iterrows():
                    sdf_pts.append((float(r.iloc[0]), float(r.iloc[1]), str(r.iloc[2]) if r.shape[0]>2 else "SDF"))
            except Exception as e:
                st.error(f"Failed to parse SDF CSV: {e}")

        # Obstacles overlay
        obstacles = []
        if obs_csv is not None:
            try:
                obs_df = pd.read_csv(obs_csv)
                for _, r in obs_df.iterrows():
                    obstacles.append((float(r.iloc[0]), float(r.iloc[1]), str(r.iloc[2]) if r.shape[0]>2 else "OBS"))
            except Exception as e:
                st.error(f"Failed to parse obstacles CSV: {e}")

        terrain_ft = [c["elev_ft"] if c.get("elev_ft") is not None else 0 for c in coords]

        # Collision & MDA checks
        coll_pts, below_mda_pts = [], []
        for i, alt in enumerate(alt_profile_ft):
            t = terrain_ft[i] if terrain_ft[i] is not None else 0
            if alt <= t + safety_buffer_ft:
                coll_pts.append((dists[i], alt, t))
            if alt < mda_ft:
                below_mda_pts.append((dists[i], alt))

        # DME table calculation (linear between FAF and MDA/DA)
        target_alt_at_dme = None
        if 0.0 <= dme_dist <= faf_to_thr_nm:
            frac = (faf_to_thr_nm - dme_dist) / max(faf_to_thr_nm, 1e-6)
            target_alt_at_dme = faf_alt_ft - (faf_alt_ft - mda_ft) * frac

        # ---- Static profile plot ----
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=dists, y=alt_profile_ft, mode='lines', name='CDFA'))
        fig.add_trace(go.Scatter(x=dists, y=terrain_ft, mode='lines', name='Terrain', fill='tozeroy', opacity=0.5))
        if obstacles:
            fig.add_trace(go.Scatter(x=[o[0] for o in obstacles], y=[o[1] for o in obstacles],
                                     mode='markers+text', text=[o[2] for o in obstacles],
                                     textposition='top center', name='Obstacles'))
        if sdf_pts:
            fig.add_trace(go.Scatter(x=[s[0] for s in sdf_pts], y=[s[1] for s in sdf_pts],
                                     mode='markers+text', text=[s[2] for s in sdf_pts],
                                     textposition='bottom center', name='Step-down fixes'))
        if coll_pts:
            fig.add_trace(go.Scatter(x=[p[0] for p in coll_pts], y=[p[1] for p in coll_pts],
                                     mode='markers', name='Collision risk'))
        fig.add_hline(y=mda_ft, line_dash='dash', annotation_text=f"MDA/DA {mda_ft:.0f} ft", annotation_position='top left')
        fig.update_xaxes(title="Distance from threshold (NM)", autorange='reversed')
        fig.update_yaxes(title="Altitude / Terrain (ft)")
        st.plotly_chart(fig, use_container_width=True, key="static_profile_main")

        # ---- Animation ----
        anim_ph = st.empty()
        for idx in range(len(dists)):
            frame_fig = go.Figure()
            frame_fig.add_trace(go.Scatter(x=dists, y=alt_profile_ft, mode='lines', name='CDFA'))
            frame_fig.add_trace(go.Scatter(x=dists, y=terrain_ft, mode='lines', name='Terrain', fill='tozeroy', opacity=0.5))
            frame_fig.add_trace(go.Scatter(x=[dists[idx]], y=[alt_profile_ft[idx]], mode='markers', name='Aircraft'))
            if obstacles:
                frame_fig.add_trace(go.Scatter(x=[o[0] for o in obstacles], y=[o[1] for o in obstacles],
                                               mode='markers', name='Obstacles'))
            if coll_pts:
                frame_fig.add_trace(go.Scatter(x=[p[0] for p in coll_pts], y=[p[1] for p in coll_pts],
                                               mode='markers', name='Collision risk'))
            frame_fig.add_hline(y=mda_ft, line_dash='dash')
            frame_fig.update_xaxes(autorange='reversed')
            frame_fig.update_yaxes(autorange=True)
            frame_fig.update_layout(height=480, title=f"Frame {idx+1}/{len(dists)} • DME {dists[idx]:.2f} NM • ALT {alt_profile_ft[idx]:.0f} ft")
            anim_ph.plotly_chart(frame_fig, use_container_width=True, key=f"anim_frame_{idx}")
            time.sleep(frame_delay)

        # ---- DME readout ----
        if target_alt_at_dme is not None:
            st.info(f"Target altitude at DME {dme_dist:.2f} NM ≈ **{target_alt_at_dme:.0f} ft**")

        st.success("Simulation complete ✅")

else:
    st.info("Configure inputs on the left and click **Run Simulation**. Upload Obstacles/Step-down CSVs if needed.")
