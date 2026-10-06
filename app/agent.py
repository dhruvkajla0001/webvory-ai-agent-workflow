from __future__ import annotations

from pathlib import Path
from typing import Any

from .excel_loader import load_workflows
from .llm import build_llm
from .models import AgentResult
from .tools.builtins import build_tool_registry
from .workflows import WorkflowHandlers


class WorkflowAgent:
    """
    Single reusable agent:
      1. loads workflow specifications from Excel
      2. selects one workflow from the user request
      3. delegates execution to registered reusable tools
      4. returns an auditable execution trace

    Adding a workflow does not require a new chatbot or agent.
    """

    def __init__(self, excel_path: str | Path, data_dir: str | Path):
        self.excel_path = str(excel_path)
        self.data_dir = str(data_dir)
        self.workflows = load_workflows(excel_path)
        self.llm = build_llm()
        self.tools = build_tool_registry(self.data_dir)
        self.handlers = WorkflowHandlers(self.tools, self.data_dir, self.llm)

    def run(self, request: str, context: dict[str, Any] | None = None) -> AgentResult:
        workflow_id, reason = self.llm.select_workflow(request, list(self.workflows.values()))
        if workflow_id not in self.workflows:
            return AgentResult(
                request=request, status="failed",
                selection_reason=reason,
                errors=["Could not confidently select a supported workflow."],
            )
        spec = self.workflows[workflow_id]
        result = self.handlers.run(workflow_id, request, context)
        result.selected_workflow = spec.workflow_name
        result.selection_reason = reason
        return result
