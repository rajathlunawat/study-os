"""
StudyOS Main FastAPI Application Entrypoint.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# In a real app, you would import the router here
# from app.api.router import api_router

app = FastAPI(
    title="StudyOS API",
    description="Backend API for the StudyOS AI Operating System for Students",
    version="1.0.0",
)

# CORS middleware for the Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the main API router
# app.include_router(api_router, prefix="/api")

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "StudyOS Backend is running"}
