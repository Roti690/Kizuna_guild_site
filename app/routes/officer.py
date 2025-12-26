from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import select
from urllib.parse import quote
import json

from ..db import get_db
from ..models import Member, EventConfig, Guide, GuideImage
from ..config import settings

import os, re, time
from fastapi import UploadFile, File



router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

ALLOWED = {"holiday", "inactive", "low", "active"}
ACTIVITY_WEEKS = 8
UPLOAD_DIR = "app/static/uploads"
ALLOWED_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif"}

def slugify(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return s or f"guide-{int(time.time())}"
    
def require_officer(request: Request):
    if not request.session.get("is_officer"):
        return RedirectResponse(url="/officer/login", status_code=303)
    return None

def parse_activity_history(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if not isinstance(data, list):
        return []
    return [s for s in data if isinstance(s, str) and s in ALLOWED]

def build_activity_trend(member: Member) -> list[str]:
    max_history = max(ACTIVITY_WEEKS - 2, 0)
    history = parse_activity_history(member.activity_history)
    history = history[-max_history:]
    statuses = history + [member.week2_status, member.week1_status]
    if len(statuses) < ACTIVITY_WEEKS:
        statuses = ["unknown"] * (ACTIVITY_WEEKS - len(statuses)) + statuses
    return statuses



@router.get("/_officer", response_class=HTMLResponse)
def officer_panel(request: Request, db: Session = Depends(get_db)):
    gate = require_officer(request)
    if gate:
        return gate

    members = db.scalars(select(Member).order_by(Member.role.desc(), Member.name.asc())).all()
    for m in members:
        m.activity_trend = build_activity_trend(m)

    cfg = db.get(EventConfig, 1)
    if not cfg:
        cfg = EventConfig(id=1)
        db.add(cfg)
        db.commit()
        db.refresh(cfg)

    guides = db.scalars(select(Guide).order_by(Guide.category.asc(), Guide.title.asc())).all()

    return templates.TemplateResponse(
        "officer.html",
        {
            "request": request,
            "is_officer": True,
            "app_name": settings.app_name,
            "members": members,
            "guides": guides,
            "allowed": sorted(ALLOWED),
            "cfg": cfg,
            "activity_weeks": ACTIVITY_WEEKS,
        },
    )



@router.post("/_officer/roll-week")
def roll_week(
    default_new_week1: str = Form("active"),
    db: Session = Depends(get_db),
):
    default_new_week1 = default_new_week1.strip().lower()
    if default_new_week1 not in ALLOWED:
        raise HTTPException(status_code=400, detail="Invalid status")

    members = db.scalars(select(Member)).all()
    for m in members:
        history = parse_activity_history(m.activity_history)
        history.append(m.week2_status if m.week2_status in ALLOWED else "unknown")
        max_history = max(ACTIVITY_WEEKS - 2, 0)
        history = history[-max_history:]
        m.activity_history = json.dumps(history)
        m.week2_status = m.week1_status
        m.week1_status = default_new_week1
    db.commit()

    return RedirectResponse(url=f"/_officer", status_code=303)

@router.post("/_officer/add")
def add_member(
    name: str = Form(...),
    role: str = Form("Member"),
    week1_status: str = Form("active"),
    week2_status: str = Form("active"),
    note: str = Form(""),
    db: Session = Depends(get_db),
):
    

    name = name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Name required")

    week1_status = week1_status.strip().lower()
    week2_status = week2_status.strip().lower()
    if week1_status not in ALLOWED or week2_status not in ALLOWED:
        raise HTTPException(status_code=400, detail="Invalid status")

    existing = db.scalar(select(Member).where(Member.name == name))
    if existing:
        raise HTTPException(status_code=409, detail="Member already exists")

    m = Member(
        name=name,
        role=role.strip() or "Member",
        week1_status=week1_status,
        week2_status=week2_status,
        note=(note.strip() or None),
    )
    db.add(m)
    db.commit()

    return RedirectResponse(url=f"/_officer", status_code=303)

@router.post("/_officer/update/{member_id}")
def update_member(
    member_id: int,
    role: str = Form("Member"),
    week1_status: str = Form("active"),
    week2_status: str = Form("active"),
    note: str = Form(""),
    db: Session = Depends(get_db),
):

    m = db.get(Member, member_id)
    if not m:
        raise HTTPException(status_code=404, detail="Member not found")

    week1_status = week1_status.strip().lower()
    week2_status = week2_status.strip().lower()
    if week1_status not in ALLOWED or week2_status not in ALLOWED:
        raise HTTPException(status_code=400, detail="Invalid status")

    m.role = role.strip() or "Member"
    m.week1_status = week1_status
    m.week2_status = week2_status
    m.note = note.strip() or None
    db.commit()

    return RedirectResponse(url=f"/_officer", status_code=303)

@router.post("/_officer/update-all")
def update_all_members(
    member_id: list[int] = Form(...),
    role: list[str] = Form(...),
    week1_status: list[str] = Form(...),
    week2_status: list[str] = Form(...),
    note: list[str] = Form(...),
    db: Session = Depends(get_db),
):

    if not (len(member_id) == len(role) == len(week1_status) == len(week2_status) == len(note)):
        raise HTTPException(status_code=400, detail="Invalid payload")

    for idx, mid in enumerate(member_id):
        m = db.get(Member, mid)
        if not m:
            continue

        w1 = week1_status[idx].strip().lower()
        w2 = week2_status[idx].strip().lower()
        if w1 not in ALLOWED or w2 not in ALLOWED:
            raise HTTPException(status_code=400, detail="Invalid status")

        m.role = role[idx].strip() or "Member"
        m.week1_status = w1
        m.week2_status = w2
        note_val = note[idx].strip()
        m.note = note_val or None

    db.commit()
    return RedirectResponse(url=f"/_officer", status_code=303)

@router.post("/_officer/delete/{member_id}")
def delete_member(member_id: int, db: Session = Depends(get_db)):
    m = db.get(Member, member_id)
    if m:
        db.delete(m)
        db.commit()
    return RedirectResponse(url=f"/_officer", status_code=303)

@router.post("/_officer/events/update")
def update_events(
    breaking_sat: str = Form(...),
    breaking_sun: str = Form(...),
    skill_sat: str = Form(...),
    skill_sun: str = Form(...),
    party_daily: str = Form(...),
    raids_sat: str = Form(...),
    raids_sun: str = Form(...),
    db: Session = Depends(get_db),
):

    cfg = db.get(EventConfig, 1)
    if not cfg:
        cfg = EventConfig(id=1)
        db.add(cfg)

    cfg.breaking_sat = breaking_sat.strip()
    cfg.breaking_sun = breaking_sun.strip()
    cfg.skill_sat = skill_sat.strip()
    cfg.skill_sun = skill_sun.strip()
    cfg.party_daily = party_daily.strip()
    cfg.raids_sat = raids_sat.strip()
    cfg.raids_sun = raids_sun.strip()

    db.commit()
    return RedirectResponse(url=f"/_officer", status_code=303)

@router.post("/_officer/guides/{guide_id}/upload")
def upload_guide_image(
    guide_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):

    guide = db.get(Guide, guide_id)
    if not guide:
        raise HTTPException(status_code=404, detail="Guide not found")

    os.makedirs(UPLOAD_DIR, exist_ok=True)

    filename = (file.filename or "").strip()
    _, ext = os.path.splitext(filename.lower())
    if ext not in ALLOWED_EXT:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    base = slugify(os.path.splitext(filename)[0])
    out_name = f"{base}-{int(time.time())}{ext}"
    out_path = os.path.join(UPLOAD_DIR, out_name)

    with open(out_path, "wb") as f:
        f.write(file.file.read())

    url = f"/static/uploads/{out_name}"

    img = GuideImage(guide_id=guide.id, path=url)
    db.add(img)
    db.commit()

    return RedirectResponse(
        url=f"/_officer/guides/edit/{guide.id}",
        status_code=303,
    )


@router.post("/_officer/guides/create")
def create_guide(
    title: str = Form(...),
    category: str = Form("general"),
    summary: str = Form(""),
    content_md: str = Form(""),
    cover_file: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):

    category = category.strip().lower()
    if category not in {"general", "build"}:
        raise HTTPException(status_code=400)

    slug = slugify(title)
    if db.scalar(select(Guide).where(Guide.slug == slug)):
        slug = f"{slug}-{int(time.time())}"

    cover_image = None
    if cover_file and cover_file.filename:
        cover_image = _save_upload_and_get_url(cover_file)

    g = Guide(
        title=title.strip(),
        slug=slug,
        category=category,
        summary=summary.strip(),
        cover_image=cover_image,
        content_md=content_md,
    )
    db.add(g)
    db.commit()
    db.refresh(g)

    return RedirectResponse(
        url=f"/_officer/guides/edit/{g.id}",
        status_code=303,
    )


@router.get("/_officer/guides", response_class=HTMLResponse)
def guides_list(request: Request, db: Session = Depends(get_db)):
    gate = require_officer(request)
    if gate:
        return gate
    guides = db.scalars(select(Guide).order_by(Guide.category.asc(), Guide.title.asc())).all()
    return templates.TemplateResponse(
        "officer_guides.html",
        {
            "request": request,
            "is_officer": True,
            "app_name": settings.app_name,
            "guides": guides,
        },
    )

@router.get("/_officer/guides/new", response_class=HTMLResponse)
def guides_new(request: Request):
    gate = require_officer(request)
    if gate:
        return gate
    return templates.TemplateResponse(
        "officer_guide_edit.html",
        {
            "request": request,
            "is_officer": True,
            "app_name": settings.app_name,
            "mode": "create",
            "guide": None,
        },
    )



@router.get("/_officer/guides/edit/{guide_id}", response_class=HTMLResponse)
def guides_edit(guide_id: int, request: Request, db: Session = Depends(get_db)):
    gate = require_officer(request)
    if gate:
        return gate
    guide = db.get(Guide, guide_id)
    if not guide:
        raise HTTPException(status_code=404)

    images = db.scalars(
        select(GuideImage).where(GuideImage.guide_id == guide.id)
    ).all()

    return templates.TemplateResponse(
        "officer_guide_edit.html",
        {
            "request": request,
            "is_officer": True,
            "app_name": settings.app_name,
            "guide": guide,
            "images": images,
        },
    )

@router.post("/_officer/guides/update/{guide_id}")
def update_guide(
    guide_id: int,
    title: str = Form(...),
    category: str = Form(...),
    summary: str = Form(""),
    content_md: str = Form(""),
    cover_file: UploadFile | None = File(None),
    remove_cover: str | None = Form(None),
    db: Session = Depends(get_db),
):

    g = db.get(Guide, guide_id)
    if not g:
        raise HTTPException(status_code=404, detail="Guide not found")

    category = category.strip().lower()
    if category not in {"general", "build"}:
        raise HTTPException(status_code=400, detail="Invalid category")

    g.title = title.strip()
    g.category = category
    g.summary = summary.strip()
    g.content_md = content_md

    if remove_cover:
        g.cover_image = None

    if cover_file and cover_file.filename:
        g.cover_image = _save_upload_and_get_url(cover_file)

    db.commit()
    return RedirectResponse(url=f"/_officer/guides/edit/{guide_id}", status_code=303)


@router.post("/_officer/guides/delete/{guide_id}")
def delete_guide(guide_id: int, db: Session = Depends(get_db)):
    g = db.get(Guide, guide_id)
    if g:
        db.delete(g)
        db.commit()
    return RedirectResponse(url=f"/_officer/guides", status_code=303)

def _save_upload_and_get_url(file: UploadFile) -> str:
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    filename = (file.filename or "").strip()
    _, ext = os.path.splitext(filename.lower())
    if ext not in ALLOWED_EXT:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    safe_base = slugify(os.path.splitext(filename)[0])
    out_name = f"{safe_base}-{int(time.time())}{ext}"
    out_path = os.path.join(UPLOAD_DIR, out_name)

    with open(out_path, "wb") as f:
        f.write(file.file.read())

    return f"/static/uploads/{out_name}"
