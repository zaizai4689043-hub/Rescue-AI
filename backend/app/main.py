from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.api.v1.router import router as v1_router

# 确保模型被导入，以便 Base.metadata 知道它们
from app.models import User, Disaster, Resource, Volunteer, Assessment, TrappedPerson, SocialPost  # noqa: F401

app = FastAPI(title="AI地震救援平台", version="1.0.0")

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载 v1 路由
app.include_router(v1_router, prefix="/api/v1")


@app.on_event("startup")
async def on_startup():
    Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {"message": "AI地震救援平台 API", "docs": "/docs"}
