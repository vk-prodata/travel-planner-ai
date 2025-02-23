# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from travel_planner_ai.backend.routes import router as trip_router
from .config.logging_config import setup_logging

app = FastAPI(title="Travel Planner AI")

# Configure CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React app URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

app.include_router(trip_router, prefix="/api")

# Setup logging at application startup
setup_logging()

# Add cookie middleware
@app.middleware("http")
async def add_secure_cookie_settings(request, call_next):
    response = await call_next(request)
    if response.headers.get("set-cookie"):
        response.headers["set-cookie"] += "; SameSite=Strict; Secure"
    return response

@app.get("/")
async def root():
    return {"message": "Welcome to Travel Planner AI API"}

# Run with: uvicorn main:app --reload
