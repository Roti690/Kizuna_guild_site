from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from .db import Base, engine, ensure_member_activity_history
from .routes.pages import router as pages_router
from .routes.api import router as api_router
from .config import settings
from .routes.officer import router as officer_router
from .routes import auth

def create_app() -> FastAPI:
    app = FastAPI(title=f"{settings.app_name} Guild Site")

    # Create tables
    Base.metadata.create_all(bind=engine)
    ensure_member_activity_history()

    app.mount("/static", StaticFiles(directory="app/static"), name="static")

    app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret,  # add to settings below
    same_site="lax",
    https_only=False  # set True when you deploy behind HTTPS
    )
    
    app.include_router(pages_router)
    app.include_router(api_router)
    app.include_router(officer_router)
    app.include_router(auth.router)


    return app

app = create_app()
