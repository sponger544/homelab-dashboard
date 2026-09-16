import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse

from app.db import init_db, is_setup_complete
from app.api.dashboard import router as dashboard_router
from app.api.admin import router as admin_router
from app.api.wizard import router as wizard_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database on startup
    await init_db()
    yield

app = FastAPI(title="Home Lab Dashboard", lifespan=lifespan)

# Mount static files
app.mount("/static", StaticFiles(directory="/app/app/static"), name="static")
app.mount("/uploads", StaticFiles(directory="/app/uploads"), name="uploads")

# Setup templates
templates = Jinja2Templates(directory="/app/app/templates")

# Include routers
app.include_router(dashboard_router, prefix="/api/stats", tags=["stats"])
app.include_router(admin_router, prefix="/api/admin", tags=["admin"])
app.include_router(wizard_router, prefix="/api/wizard", tags=["wizard"])

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

@app.get("/api/needs-setup")
async def check_setup():
    complete = await is_setup_complete()
    return {"needs_setup": not complete}

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Main page - redirect to wizard if not set up, otherwise dashboard."""
    complete = await is_setup_complete()
    if not complete:
        return templates.TemplateResponse("wizard.html", {"request": request})
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    """Admin panel."""
    return templates.TemplateResponse("admin.html", {"request": request})
