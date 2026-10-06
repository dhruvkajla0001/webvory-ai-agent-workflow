from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field


class WorkflowSpec(BaseModel):
    workflow_id: str
    workflow_name: str
    trigger: str
    inputs: str
    steps: list[str]
    decision_logic: str
    tools_required: list[str]
    expected_output: str


class ExecutionStep(BaseModel):
    step: int
    action: str
    tool: str | None = None
    status: Literal["success", "skipped", "failed"] = "success"
    detail: str = ""


class AgentResult(BaseModel):
    request: str
    selected_workflow_id: str | None = None
    selected_workflow: str | None = None
    selection_reason: str = ""
    status: Literal["success", "needs_input", "failed"] = "success"
    steps_executed: list[ExecutionStep] = Field(default_factory=list)
    result: Any = None
    errors: list[str] = Field(default_factory=list)
