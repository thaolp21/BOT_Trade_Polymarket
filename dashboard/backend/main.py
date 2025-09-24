from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import subprocess
import sys
import os
import importlib.util
import json

app = FastAPI()

# Allow CORS for local frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Path to your fill_template.py
FILL_TEMPLATE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../export_data/fill_template.py'))

@app.get("/api/grouped-data")
def get_grouped_data():
    # Dynamically import fill_template.py and run the logic
    spec = importlib.util.spec_from_file_location("fill_template", FILL_TEMPLATE_PATH)
    fill_template = importlib.util.module_from_spec(spec)
    sys.modules["fill_template"] = fill_template
    spec.loader.exec_module(fill_template)
    data = fill_template.get_data()
    grouped_data = fill_template.group_rounds(data)
    return grouped_data
