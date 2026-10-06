from __future__ import annotations

import argparse
import json
from pathlib import Path

from .agent import WorkflowAgent

BASE = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description="Webvory reusable AI workflow agent")
    parser.add_argument("--request", required=True, help="User request")
    parser.add_argument("--context", default="{}", help="Optional JSON context")
    args = parser.parse_args()

    agent = WorkflowAgent(BASE / "data" / "AI_Agent_Workflow_Assessment.xlsx", BASE / "data")
    context = json.loads(args.context)
    result = agent.run(args.request, context)

    print("=" * 72)
    print("WEBVORY AI AGENT WORKFLOW AUTOMATION")
    print("=" * 72)
    print(f"Selected Workflow: {result.selected_workflow_id} - {result.selected_workflow}")
    print(f"Selection Reason: {result.selection_reason}")
    print(f"Status: {result.status}")
    print("\nSteps Executed:")
    for step in result.steps_executed:
        tool = f" [{step.tool}]" if step.tool else ""
        detail = f" — {step.detail}" if step.detail else ""
        print(f"{step.step}. {step.action}{tool}{detail}")
    print("\nResult:")
    print(json.dumps(result.result, indent=2, default=str))
    if result.errors:
        print("\nErrors / Follow-up:")
        for error in result.errors:
            print(f"- {error}")


if __name__ == "__main__":
    main()
