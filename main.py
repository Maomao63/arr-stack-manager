import json
import os
from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

app = FastAPI()
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))
CONFIG_FILE = "/app/config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {"sonarr_a_url": "", "sonarr_a_api": "", "radarr_a_url": "", "radarr_a_api": ""}

@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "config": load_config()})

@app.get("/settings")
async def settings_page(request: Request):
    return templates.TemplateResponse("settings.html", {"request": request, "config": load_config()})

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
