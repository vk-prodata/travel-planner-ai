# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import router as trip_router

app = FastAPI(title="Travel Planner AI")

# Configure CORS for local development; update allowed origins in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Replace "*" with your production domain(s).
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(trip_router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Travel Planner AI API"}

# Run with: uvicorn main:app --reload
