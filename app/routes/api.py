from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session
from sqlalchemy import select

from ..db import get_db
from ..models import Member, Post

router = APIRouter(prefix="/api", tags=["api"])


ALLOWED = {"holiday", "inactive", "low", "active"}

class MemberIn(BaseModel):
    name: str
    role: str = "Member"
    week1_status: str = "active"
    week2_status: str = "active"
    note: str | None = None

    @field_validator("week1_status", "week2_status")
    @classmethod
    def validate_status(cls, v: str):
        v = v.strip().lower()
        if v not in ALLOWED:
            raise ValueError(f"status must be one of {sorted(ALLOWED)}")
        return v

class MemberUpdate(BaseModel):
    role: str | None = None
    week1_status: str | None = None
    week2_status: str | None = None
    note: str | None = None

    @field_validator("week1_status", "week2_status")
    @classmethod
    def validate_status(cls, v: str | None):
        if v is None:
            return v
        v = v.strip().lower()
        if v not in ALLOWED:
            raise ValueError(f"status must be one of {sorted(ALLOWED)}")
        return v

class PostIn(BaseModel):
    title: str
    body: str

@router.get("/members")
def list_members(db: Session = Depends(get_db)):
    return db.scalars(select(Member).order_by(Member.role.desc(), Member.name.asc())).all()

@router.post("/members")
def create_member(payload: MemberIn, db: Session = Depends(get_db)):
    existing = db.scalar(select(Member).where(Member.name == payload.name))
    if existing:
        raise HTTPException(status_code=409, detail="Member already exists")

    m = Member(
        name=payload.name,
        role=payload.role,
        week1_status=payload.week1_status,
        week2_status=payload.week2_status,
        note=payload.note,
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    return m

@router.patch("/members/{member_id}")
def update_member(member_id: int, payload: MemberUpdate, db: Session = Depends(get_db)):
    m = db.get(Member, member_id)
    if not m:
        raise HTTPException(status_code=404, detail="Member not found")

    if payload.role is not None:
        m.role = payload.role
    if payload.week1_status is not None:
        m.week1_status = payload.week1_status
    if payload.week2_status is not None:
        m.week2_status = payload.week2_status
    if payload.note is not None:
        m.note = payload.note

    db.commit()
    db.refresh(m)
    return m

@router.post("/members/roll-week")
def roll_week(default_new_week1: str = "active", db: Session = Depends(get_db)):
    default_new_week1 = default_new_week1.strip().lower()
    if default_new_week1 not in ALLOWED:
        raise HTTPException(status_code=400, detail=f"default_new_week1 must be one of {sorted(ALLOWED)}")

    members = db.scalars(select(Member)).all()
    for m in members:
        m.week2_status = m.week1_status
        m.week1_status = default_new_week1  # resets new week to something you choose
    db.commit()
    return {"ok": True, "rolled": len(members), "new_week1_default": default_new_week1}

@router.get("/posts")
def list_posts(db: Session = Depends(get_db)):
    return db.scalars(select(Post).order_by(Post.id.desc())).all()

@router.post("/posts")
def create_post(payload: PostIn, db: Session = Depends(get_db)):
    p = Post(title=payload.title, body=payload.body)
    db.add(p)
    db.commit()
    db.refresh(p)
    return p
