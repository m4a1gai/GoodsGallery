from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import catalog, collection, review, sources
from app.core.config import settings

app = FastAPI(title="GoodsGallery API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(catalog.router)
app.include_router(collection.router)
app.include_router(review.router)
app.include_router(sources.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
