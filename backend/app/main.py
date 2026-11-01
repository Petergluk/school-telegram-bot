from fastapi import FastAPI

from app.db import Base, engine
from app.routers.school import router as school_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="School MVP API")

app.include_router(school_router)


@app.get("/")
async def root():
    return {"message": "School MVP API is running"}
