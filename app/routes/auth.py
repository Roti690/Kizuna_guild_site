from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from ..config import settings
from fastapi.templating import Jinja2Templates



templates = Jinja2Templates(directory="app/templates")
router = APIRouter()

@router.get("/officer/login", response_class=HTMLResponse)
def officer_login_page(request: Request):
    return templates.TemplateResponse(
        "officer_login.html",
        {"request": request, "app_name": settings.app_name, "error": None},
    )

@router.post("/officer/login")
def officer_login(request: Request, password: str = Form(...)):
    if password != settings.officer_password:
        return templates.TemplateResponse(
            "officer_login.html",
            {"request": request, "app_name": settings.app_name, "error": "Wrong password."},
            status_code=401,
        )

    request.session["is_officer"] = True
    return RedirectResponse(url="/_officer", status_code=303)

@router.post("/officer/logout")
def officer_logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)
