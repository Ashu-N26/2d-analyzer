
import srtm
import math
import argparse

def precache_box(lat_center, lon_center, km_radius=20, step_km=1.0):
    data = srtm.get_data()
    lat_step = step_km / 111.0
    lon_step = step_km / 111.0
    n = int((2*km_radius) / step_km)
    for i in range(-n, n+1):
        for j in range(-n, n+1):
            lat = lat_center + i*lat_step
            lon = lon_center + j*lon_step
            try:
                _ = data.get_elevation(lat, lon)
            except Exception:
                pass
    print("SRTM pre-cache complete.")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--lat", type=float, required=True)
    p.add_argument("--lon", type=float, required=True)
    p.add_argument("--radius_km", type=float, default=20)
    args = p.parse_args()
    precache_box(args.lat, args.lon, km_radius=args.radius_km)
