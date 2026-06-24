from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routes.artifacts import router as artifacts_router
from app.routes.files import router as files_router
from app.routes.health import router as health_router
from app.routes.llm import router as llm_router
from app.routes.registries import router as registries_router
from app.routes.runs import router as runs_router


app = FastAPI(title="Agent Harness API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3005"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(runs_router)
app.include_router(registries_router)
app.include_router(llm_router)
app.include_router(files_router)
app.include_router(artifacts_router)


@app.get("/")
def root() -> dict[str, str]:
    return {"service": settings.service_name}
