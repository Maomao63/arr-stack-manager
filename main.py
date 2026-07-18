import json
import os
from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from jinja2 import Environment, FileSystemLoader

app = FastAPI()

# Wir erstellen eine eigene Jinja2-Umgebung ohne Cache
# Das verhindert, dass Jinja2 versucht, Requests zu cachen
env = Environment(loader=FileSystemLoader("templates"), cache_size=0)
templates = Jinja2Templates(directory="templates")
templates.env = env

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

@app.get("/")
async def read_root(request: Request):
    c = load_config()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "sonarr_a_url": c.get("sonarr_a_url", ""),
        "sonarr_a_api": c.get("sonarr_a_api", ""),
        "radarr_a_url": c.get("radarr_a_url", ""),
        "radarr_a_api": c.get("radarr_a_api", "")
    })

@app.get("/settings")
async def settings_page(request: Request):
    c = load_config()
    return templates.TemplateResponse("settings.html", {
        "request": request,
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
