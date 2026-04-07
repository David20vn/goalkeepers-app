from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import (
    auth_router,
    user_router,
    goalkeeper_router,
    match_router,
    offer_router,
    rating_router
)

from app.core.config import settings


def create_application() -> FastAPI:

    app = FastAPI(
        title=settings.PROJECT_NAME,
        version="1.0.0",
        description="Marketplace de contratación de arqueros para partidos amateur"
    )

    # CORS (permite conexión con frontend)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    app.include_router(auth_router.router, prefix="/auth", tags=["Auth"])
    app.include_router(user_router.router, prefix="/users", tags=["Users"])
    app.include_router(goalkeeper_router.router, prefix="/goalkeepers", tags=["Goalkeepers"])
    app.include_router(match_router.router, prefix="/matches", tags=["Matches"])
    app.include_router(offer_router.router, prefix="/offers", tags=["Offers"])
    app.include_router(rating_router.router, prefix="/ratings", tags=["Ratings"])

    # Health Check
    @app.get("/")
    def root():
        return {"message": "Marketplace Arqueros API Running"}

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_application()