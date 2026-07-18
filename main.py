import json
import os
from fastapi import FastAPI, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse

app = FastAPI()
templates = Jinja2Templates(directory="templates")
CONFIG_FILE = "/app/config.json"

def load_config():
    default = {"sonarr_a_url": "", "sonarr_a_api": "", "radarr_a_url": "", "radarr_a_api": ""}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except:
            return default
    return default

@app.get("/", response_class=HTMLResponse)
async def read_root():
    c = load_config()
    # Wir übergeben KEINEN 'request' mehr, um den Hash-Fehler zu vermeiden
    return templates.TemplateResponse("index.html", {
        "sonarr_a_url": c.get("sonarr_a_url", ""),
        "sonarr_a_api": c.get("sonarr_a_api", ""),
        "radarr_a_url": c.get("radarr_a_url", ""),
        "radarr_a_api": c.get("radarr_a_api", "")
    })

@app.get("/settings", response_class=HTMLResponse)
async def settings_page():
    c = load_config()
    return templates.TemplateResponse("settings.html", {
        "sonarr_a_url": c.get("sonarr_a_url", ""),
        "sonarr_a_api": c.get("sonarr_a_api", ""),
        "radarr_a_url": c.get("radarr_a_url", ""),
        "radarr_a_api": c.get("radarr_a_api", "")
    })

@app.post("/save-config")
async def save_config(
    sonarr_a_url: str = Form(""), sonarr_a_api: str = Form(""),
    radarr_a_url: str = Form(""), radarr_a_api: str = Form("")
):
    config = {
        "sonarr_a_url": sonarr_a_url, "sonarr_a_api": sonarr_a_api,
        "radarr_a_url": radarr_a_url, "radarr_a_api": radarr_a_api
    }
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)
    return RedirectResponse(url="/", status_code=303)
