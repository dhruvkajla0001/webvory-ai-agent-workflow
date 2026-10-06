from pathlib import Path
from app.agent import WorkflowAgent

BASE = Path(__file__).resolve().parents[1]
agent = WorkflowAgent(BASE / "data" / "AI_Agent_Workflow_Assessment.xlsx", BASE / "data")


def test_all_ten_workflows_loaded():
    assert len(agent.workflows) == 10
    assert set(agent.workflows) == {f"WF{i:03d}" for i in range(1, 11)}


def test_wf001_restock():
    r = agent.run("Which products need restocking?")
    assert r.selected_workflow_id == "WF001"
    assert len(r.result["products_requiring_restock"]) == 3


def test_wf002_price_exceptions():
    r = agent.run("Find products where vendor price differs by more than 10%.")
    assert r.selected_workflow_id == "WF002"
    assert r.result["exception_count"] == 2


def test_wf003_invalid_rows():
    r = agent.run("Process this vendor spreadsheet and show invalid rows.")
    assert r.selected_workflow_id == "WF003"
    assert r.result["validation_summary"]["invalid_rows"] == 2
    assert r.result["validation_summary"]["valid_rows"] == 2


def test_wf004_generation():
    r = agent.run("Generate SEO content for this product.")
    assert r.selected_workflow_id == "WF004"
    assert "seo_title" in r.result


def test_wf005_order():
    r = agent.run("Where is order ORD-1001?")
    assert r.selected_workflow_id == "WF005"
    assert r.result["status"] == "Shipped"


def test_wf005_missing_order():
    r = agent.run("Where is order ORD-9999?")
    assert r.selected_workflow_id == "WF005"
    assert r.status == "needs_input"
    assert r.errors


def test_wf006_duplicates():
    r = agent.run("Find likely duplicate products in the catalog.")
    assert r.selected_workflow_id == "WF006"
    assert len(r.result["duplicate_groups"]) >= 2


def test_wf007_missing_inputs():
    r = agent.run("Create a campaign brief for the new collection.")
    assert r.selected_workflow_id == "WF007"
    assert r.status == "needs_input"


def test_wf007_success():
    r = agent.run(
        "Create a campaign brief for the new collection.",
        {"goal": "Increase launch sales", "audience": "urban professionals",
         "promotion": "15% launch discount", "dates": "Oct 10–Oct 20"}
    )
    assert r.selected_workflow_id == "WF007"
    assert "objective" in r.result


def test_wf008_keywords():
    r = agent.run("Classify these keywords and map them to pages.")
    assert r.selected_workflow_id == "WF008"
    assert len(r.result["keyword_report"]) == 7


def test_wf009_assignment():
    r = agent.run(
        "Assign this urgent task to the best available developer.",
        {"task_description": "Build a FastAPI endpoint",
         "skills": ["python", "fastapi"], "priority": "urgent", "deadline": "2026-10-10"}
    )
    assert r.selected_workflow_id == "WF009"
    assert r.result["recommended_employee"] in {"Aarav Singh", "Ishita Kapoor"}


def test_wf009_escalation():
    r = agent.run(
        "Assign this urgent task to the best available developer.",
        {"task_description": "Build a Rust compiler", "skills": ["rust"],
         "priority": "urgent", "deadline": "2026-10-10"}
    )
    assert r.selected_workflow_id == "WF009"
    assert r.status == "needs_input"
    assert "Escalation" in r.errors[0]


def test_wf010_report():
    r = agent.run("Which workflows are failing most often?")
    assert r.selected_workflow_id == "WF010"
    assert r.result["performance_report"]


def test_new_workflow_is_data_driven_at_selection_layer():
    # The agent reads the Excel registry at runtime rather than hard-coding
    # workflow names in the API surface.
    assert all(w.trigger for w in agent.workflows.values())
