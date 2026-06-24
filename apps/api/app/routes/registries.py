from fastapi import APIRouter

from app.registries.modules import ModuleDefinition, list_modules
from app.registries.skills import SkillDefinition, list_skills
from app.registries.tools import ToolDefinition, list_tools


router = APIRouter(prefix="/api", tags=["registries"])


@router.get("/modules", response_model=list[ModuleDefinition])
def get_modules() -> list[ModuleDefinition]:
    return list_modules()


@router.get("/skills", response_model=list[SkillDefinition])
def get_skills() -> list[SkillDefinition]:
    return list_skills()


@router.get("/tools", response_model=list[ToolDefinition])
def get_tools() -> list[ToolDefinition]:
    return list_tools()
