from fastapi import FastAPI
from app.api import offer_routes, match_routes

app = FastAPI()

app.include_router(offer_routes.router)
app.include_router(match_routes.router)