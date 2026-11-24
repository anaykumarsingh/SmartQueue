import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.tokens import router as token_router
from app.api.services import router as service_router
from app.api.queue import router as queue_router
from app.api.staff import router as staff_router
from app.api.display import router as display_router
from app.api.analytics import router as analytics_router
from app.api.counters import router as counter_router
from app.api.auth import router as auth_router


app = FastAPI(
    title="SmartQueue API",
    description="Digital Queue Management and Waiting-Time Optimization System",
    version="0.1.0",
)

allowed_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

frontend_url = os.getenv("FRONTEND_URL", "").strip().rstrip("/")

if frontend_url:
    allowed_origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(token_router)
app.include_router(service_router)
app.include_router(queue_router)
app.include_router(staff_router)
app.include_router(display_router)
app.include_router(analytics_router)
app.include_router(counter_router)
app.include_router(auth_router)


@app.get("/")
def root():
    return {
        "message": "SmartQueue API is running",
        "project": "SmartQueue",
        "version": "0.1.0",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}
