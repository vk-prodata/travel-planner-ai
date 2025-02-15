# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from travel_planner_ai.backend.routes import router as trip_router

app = FastAPI(title="Travel Planner AI")

# Configure CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React app URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(trip_router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "Welcome to Travel Planner AI API"}

# Run with: uvicorn main:app --reload
