from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from .services.auth import get_current_user
from .models.user import User

web_router = APIRouter()
templates = Jinja2Templates(directory="MRI/app/templates")

@web_router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """首页"""
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )

@web_router.get("/online-training", response_class=HTMLResponse)
async def online_training(request: Request, current_user: User = Depends(get_current_user)):
    """在线训练页面"""
    return templates.TemplateResponse(
        "online_training.html",
        {"request": request, "user": current_user}
    ) 