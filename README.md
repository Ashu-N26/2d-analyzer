# IAC 2D Visual Analyzer

A web-based Streamlit tool to visualize aircraft flying an instrument approach in 2D.

## Features
- Side-view descent profile
- Step-down fix support
- MDA/DA safety check alerts
- Moving aircraft animation

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy to Render
1. Push this repo to GitHub
2. Create new Web Service on Render
3. Use `Dockerfile` for deployment
4. Set port to 8501
