from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field

from .agent import WorkflowAgent

BASE = Path(__file__).resolve().parents[1]
EXCEL = BASE / "data" / "AI_Agent_Workflow_Assessment.xlsx"
DATA = BASE / "data"

agent = WorkflowAgent(EXCEL, DATA)
app = FastAPI(title="Webvory AI Agent Workflow Automation", version="1.0.0")


class AgentRequest(BaseModel):
    request: str
    context: dict[str, Any] = Field(default_factory=dict)


@app.get("/health")
def health():
    return {"status": "ok", "workflows_loaded": len(agent.workflows), "tools": agent.tools.list_tools()}


@app.get("/workflows")
def workflows():
    return [
        {
            "workflow_id": w.workflow_id,
            "workflow_name": w.workflow_name,
            "trigger": w.trigger,
            "inputs": w.inputs,
            "steps": w.steps,
            "decision_logic": w.decision_logic,
            "tools_required": w.tools_required,
            "expected_output": w.expected_output,
        }
        for w in agent.workflows.values()
    ]


@app.post("/agent/run")
def run_agent(payload: AgentRequest):
    return agent.run(payload.request, payload.context).model_dump()
