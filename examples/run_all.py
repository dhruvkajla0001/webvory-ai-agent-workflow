import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

from app.agent import WorkflowAgent


agent = WorkflowAgent(
    BASE / "data" / "AI_Agent_Workflow_Assessment.xlsx",
    BASE / "data"
)

for item in json.loads((BASE / "examples" / "requests.json").read_text()):
    result = agent.run(
        item["request"],
        item.get("context", {})
    )

    print("\n" + "=" * 70)
    print(item["request"])
    print(f"Selected: {result.selected_workflow_id} | Status: {result.status}")
    print(json.dumps(result.result, indent=2, default=str))

    if result.errors:
        print("Errors:", result.errors)