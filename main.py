import json
import os
from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

app = FastAPI()
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))
CONFIG_FILE = "/app/config.json"

def load_config():
    default_config = {"sonarr_a_url": "", "sonarr_a_api": "", "radarr_a_url": "", "radarr_a_api": ""}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else default_config
        except Exception:
            return default_config
    return default_config

@app.get("/")
async def read_root(request: Request):
    # Config vorher laden, damit wir ein sauberes Dict haben
    config_data = load_config()
    return templates.TemplateResponse("index.html", {"request": request, "config": config_data})

@app.get("/settings")
async def settings_page(request: Request):
    # Config vorher laden, damit wir ein sauberes Dict haben
    config_data = load_config()
    return templates.TemplateResponse("settings.html", {"request": request, "config": config_data})

@app.post("/save-config")
async def save_config(
    sonarr_a_url: str = Form(...), sonarr_a_api: str = Form(...),
    radarr_a_url: str = Form(...), radarr_a_api: str = Form(...)
):
    config = {
        "sonarr_a_url": sonarr_a_url, "sonarr_a_api": sonarr_a_api,
        "radarr_a_url": radarr_a_url, "radarr_a_api": radarr_a_api
    }
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)
    return RedirectResponse(url="/", status_code=303)
