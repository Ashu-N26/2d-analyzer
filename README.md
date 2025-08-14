
# IAC 2D Visual Analyzer — Terrain & Obstacles (Pro)

Features:
- ICAO + Runway auto-fill from `airports.csv` and `runways.csv`
- Elevation sources: SRTM (offline), Open-Elevation, Google (set `GOOGLE_API_KEY`)
- MDA/DA & safety buffer checks with collision highlighting
- DME table: enter a DME distance and see target altitude
- Step-down fixes import (`dist_nm,alt_ft,label`)
- Obstacles import (`dist_nm,height_ft,label`)
- Animation of aircraft along profile, proper x-axis (distance decreasing toward threshold)

## Run locally
```bash
pip install -r requirements.txt
export GOOGLE_API_KEY="your_key_if_using_google"
streamlit run app.py
```

## Deploy on Render
- Use repo with these files
- Service type: **Web**, Runtime **Python**
- Build: `pip install -r requirements.txt`
- Start: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
- Set `GOOGLE_API_KEY` if you want Google Elevation

## CSV formats
### airports.csv
`ident,name,latitude_deg,longitude_deg,elevation_ft`

### runways.csv
`id,airport_ident,length_ft,width_ft,le_ident,le_latitude_deg,le_longitude_deg,he_ident,he_latitude_deg,he_longitude_deg,le_heading_deg,he_heading_deg`

### Obstacle CSV
`dist_nm,height_ft,label`

### Step-down Fixes CSV
`dist_nm,alt_ft,label`
