
import pandas as pd

def load_airports(filepath="airports.csv"):
    try:
        return pd.read_csv(filepath, comment="#")
    except Exception:
        return None

def load_runways(filepath="runways.csv"):
    try:
        return pd.read_csv(filepath, comment="#")
    except Exception:
        return None

def find_runway(icao, rw_ident, airports_df, runways_df):
    if airports_df is None or runways_df is None:
        return None
    icao = icao.strip().upper(); rw_ident = rw_ident.strip().upper()
    rwy = runways_df[(runways_df['airport_ident'].str.upper() == icao) &
                     ((runways_df['le_ident'].str.upper() == rw_ident) | (runways_df['he_ident'].str.upper() == rw_ident))]
    if rwy.empty:
        # try number-only prefix
        num = ''.join([c for c in rw_ident if c.isdigit()])
        if num:
            rwy = runways_df[runways_df['airport_ident'].str.upper() == icao]
            rwy = rwy[(rwy['le_ident'].str.startswith(num)) | (rwy['he_ident'].str.startswith(num))]
    if rwy.empty:
        return None
    row = rwy.iloc[0]
    if str(row['le_ident']).upper() == rw_ident or (num and str(row['le_ident']).startswith(num)):
        return {"lat": float(row['le_latitude_deg']), "lon": float(row['le_longitude_deg']), "bearing_true": float(row['le_heading_deg'])}
    else:
        return {"lat": float(row['he_latitude_deg']), "lon": float(row['he_longitude_deg']), "bearing_true": float(row['he_heading_deg'])}
