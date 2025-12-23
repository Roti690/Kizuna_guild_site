from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import select
from collections import defaultdict
from ..services.wwm_news import fetch_wwm_news
from ..models import EventConfig


from ..db import get_db
from ..models import Member, Post, Guide
from ..config import settings
import markdown as md

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    # keep your local posts if you want, but add official feed:
    official_news = fetch_wwm_news(limit=6)

    posts = db.scalars(select(Post).order_by(Post.id.desc()).limit(5)).all()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "app_name": settings.app_name,
            "posts": posts,
            "official_news": official_news,
        },
    )

@router.get("/members", response_class=HTMLResponse)
def members(request: Request, db: Session = Depends(get_db)):
    members = db.scalars(select(Member).order_by(Member.name.asc())).all()

    def bucket(role: str) -> str:
        r = (role or "").strip().lower()

        # adjust these keywords if your roles differ
        if r in {"leader", "guild master", "gm"}:
            return "Leader"
        if r == "hr" or "hr" in r:
            return "HR"
        if r in {"staff", "officer", "mod", "moderator"} or "staff" in r:
            return "Staff"
        return "Members"

    grouped = defaultdict(list)
    for m in members:
        grouped[bucket(m.role)].append(m)

    # enforce order
    groups = [
        ("Leader", grouped.get("Leader", [])),
        ("HR", grouped.get("HR", [])),
        ("Staff", grouped.get("Staff", [])),
        ("Members", grouped.get("Members", [])),
    ]

    return templates.TemplateResponse(
        "members.html",
        {
            "request": request,
            "app_name": settings.app_name,
            "groups": groups,
            "week1_label": "Last week",
            "week2_label": "2 weeks ago",
        },
    )

@router.get("/events", response_class=HTMLResponse)
def events(request: Request, db: Session = Depends(get_db)):
    cfg = db.get(EventConfig, 1)
    if not cfg:
        cfg = EventConfig(id=1)
        db.add(cfg)
        db.commit()
        db.refresh(cfg)

    return templates.TemplateResponse(
        "events.html",
        {
            "request": request,
            "app_name": settings.app_name,
            "cfg": cfg,
        },
    )

@router.get("/builds", response_class=HTMLResponse)
def builds(request: Request, db: Session = Depends(get_db)):
    guides = db.scalars(select(Guide).order_by(Guide.category.asc(), Guide.title.asc())).all()
    general = [g for g in guides if (g.category or "") == "general"]
    build = [g for g in guides if (g.category or "") == "build"]

    return templates.TemplateResponse(
        "builds.html",
        {
            "request": request,
            "app_name": settings.app_name,
            "general_guides": general,
            "build_guides": build,
        },
    )

@router.get("/builds/{slug}", response_class=HTMLResponse)
def guide_detail(slug: str, request: Request, db: Session = Depends(get_db)):
    guide = db.scalar(select(Guide).where(Guide.slug == slug))
    if not guide:
        return templates.TemplateResponse(
            "guide_detail.html",
            {"request": request, "app_name": settings.app_name, "title": "Not found", "summary": "", "html": ""},
            status_code=404,
        )

    html = md.markdown(guide.content_md or "", extensions=["extra", "tables", "fenced_code"])
    return templates.TemplateResponse(
        "guide_detail.html",
        {
            "request": request,
            "app_name": settings.app_name,
            "title": guide.title,
            "summary": guide.summary,
            "cover_image": guide.cover_image,
            "html": html,
        },
    )
