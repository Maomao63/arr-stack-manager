import json
import os
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from jinja2 import Environment, FileSystemLoader

app = FastAPI()
# Jinja-Umgebung laden
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
    template = env.get_template("index.html")
    return HTMLResponse(content=template.render())

@app.get("/settings", response_class=HTMLResponse)
async def settings_page():
    c = load_config()
    template = env.get_template("settings.html")
    # Hier war der Fehler: Die Variable 'content' muss erst definiert werden!
    content = template.render(c)
    return HTMLResponse(content=content)

# Damit die 404 Fehler verschwinden, brauchen wir diese Platzhalter:
@app.get("/sonarr-data", response_class=HTMLResponse)
async def sonarr_data():
    return "<div>Sonarr Daten Bereich</div>"

@app.get("/radarr-data", response_class=HTMLResponse)
async def radarr_data():
    return "<div>Radarr Daten Bereich</div>"

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
