from fastapi import APIRouter, HTTPException, status

from app.registries.agent_template import AgentTemplate, AgentTemplateRegistry


router = APIRouter(prefix="/api/agent-templates", tags=["agent-templates"])

_loader = AgentTemplateRegistry()


@router.get("", response_model=list[AgentTemplate])
def list_agent_templates() -> list[AgentTemplate]:
    return _loader.list_templates()


@router.get("/{template_id}", response_model=AgentTemplate)
def get_agent_template(template_id: str) -> AgentTemplate:
    template = _loader.get_template(template_id)
    if template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent template not found")
    return template
