import json
import os
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from jinja2 import Environment, FileSystemLoader

app = FastAPI()
# Wir laden die Templates direkt mit Jinja2, ohne die FastAPI/Starlette-Klassen
env = Environment(loader=FileSystemLoader("templates"))
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
    # Direktes Laden und Rendern ohne Starlette-Cache
    template = env.get_template("index.html")
    return HTMLResponse(content=template.render(c))

@app.get("/settings", response_class=HTMLResponse)
async def settings_page():
    c = load_config()
    template = env.get_template("settings.html")
    return HTMLResponse(content=content) # Korrektur: hier muss es 'template.render(c)' heißen

# Hier das korrigierte settings_page für das Copy-Paste:
@app.get("/settings", response_class=HTMLResponse)
async def settings_page():
    c = load_config()
    template = env.get_template("settings.html")
    return HTMLResponse(content=template.render(c))

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
