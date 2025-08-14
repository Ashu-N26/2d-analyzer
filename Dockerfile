
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8501
# Optional: pre-cache SRTM for a default airport by setting build args
ARG PRECACHE=false
ARG PRECACHE_LAT=37.618805
ARG PRECACHE_LON=-122.375416
ARG PRECACHE_RADIUS_KM=20
RUN if [ "${PRECACHE}" = "true" ]; then python precache_srtm.py --lat ${PRECACHE_LAT} --lon ${PRECACHE_LON} --radius_km ${PRECACHE_RADIUS_KM}; else echo "Skip precache"; fi
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
