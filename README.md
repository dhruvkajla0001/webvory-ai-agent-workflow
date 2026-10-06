# Webvory – AI Agent Workflow Automation

A reusable Python agent architecture that converts the **10 workflows supplied in the Webvory Excel assignment** into executable workflows.

## What this demonstrates

- Excel is the workflow source of truth.
- One reusable `WorkflowAgent` handles all requests.
- The agent selects the correct workflow from the user's natural-language request.
- A shared `ToolRegistry` provides reusable tools such as CSV readers, calculators, validators, similarity, order lookup, and log readers.
- Each workflow produces an auditable execution trace: selected workflow → steps → tools → conditions → result.
- Business APIs are simulated with local CSV datasets so the project runs without external credentials.
- Optional OpenAI integration is available through `LLM_PROVIDER=openai`; default `mock` mode is deterministic and offline.
- Failure/condition handling is demonstrated for missing orders, missing campaign/task inputs, invalid vendor rows, and no suitable employee.
- Adding an 11th workflow does not require a new chatbot or API endpoint. The same agent, registry, executor, and tool layer are reused.

## Architecture

```text
                    ┌───────────────────────────┐
                    │       User Request        │
                    └─────────────┬─────────────┘
                                  │
                                  ▼
                    ┌───────────────────────────┐
                    │      WorkflowAgent        │
                    │  LLM / deterministic      │
                    │       selection           │
                    └─────────────┬─────────────┘
                                  │
                                  ▼
                    ┌───────────────────────────┐
                    │ Excel Workflow Registry   │
                    │ WF001 ... WF010           │
                    └─────────────┬─────────────┘
                                  │
                                  ▼
                    ┌───────────────────────────┐
                    │ Generic Workflow Executor │
                    │ + Handler Registry        │
                    └─────────────┬─────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    ▼                           ▼
          ┌──────────────────┐        ┌──────────────────┐
          │ Shared Tools     │        │ LLM Provider     │
          │ CSV/API simulator│        │ Mock / OpenAI    │
          │ calculator       │        │                  │
          │ validator        │        └──────────────────┘
          │ similarity       │
          └────────┬─────────┘
                   ▼
          ┌──────────────────┐
          │ Conditions/Error │
          │ handling         │
          └────────┬─────────┘
                   ▼
          ┌──────────────────┐
          │ Auditable Result │
          │ workflow + steps │
          │ + output/errors  │
          └──────────────────┘
```

## Project structure

```text
webvory_ai_agent_workflow/
├── app/
│   ├── agent.py              # Single reusable agent
│   ├── excel_loader.py       # Excel → workflow registry
│   ├── llm.py                # Mock + optional OpenAI provider
│   ├── main.py               # FastAPI application
│   ├── models.py             # Pydantic contracts
│   ├── workflows.py          # WF001–WF010 business handlers
│   └── tools/
│       ├── builtins.py       # Tool registration
│       ├── registry.py       # Shared tool registry
│       └── simulated.py      # Local API/data simulations
├── data/
│   ├── AI_Agent_Workflow_Assessment.xlsx
│   └── *.csv                 # Sample business data
├── examples/
│   ├── requests.json
│   └── run_all.py
├── tests/
│   └── test_workflows.py
├── docs/
├── outputs/
├── .env.example
└── requirements.txt
```

## Setup

### 1. Create environment

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Linux/macOS:

```bash
source .venv/bin/activate
```

### 2. Install

```bash
pip install -r requirements.txt
```

### 3. Run tests

```bash
pytest -q
```

Expected: all workflow tests pass.

## Run the CLI

Example:

```bash
python -m app.cli --request "Which products need restocking?"
```

Another:

```bash
python -m app.cli --request "Where is order ORD-1001?"
```

Campaign example with context:

```bash
python -m app.cli --request "Create a campaign brief for the new collection." --context "{\"goal\":\"Increase launch sales\",\"audience\":\"urban professionals\",\"promotion\":\"15% launch discount\",\"dates\":\"Oct 10-Oct 20\"}"
```

Run all 10 examples:

```bash
python examples/run_all.py
```

## Run the actual web application

```bash
uvicorn app.main:app --reload
```

Then open:

```text
http://127.0.0.1:8000/docs
```

Use `POST /agent/run`.

Example JSON:

```json
{
  "request": "Which products need restocking?",
  "context": {}
}
```

The response contains:

- selected workflow
- selection reason
- status
- every executed step
- tool used by each step
- final result
- errors/follow-up request where applicable

## Optional LLM mode

The default is deliberately offline and deterministic:

```env
LLM_PROVIDER=mock
```

For a real LLM-backed workflow selector/content generator:

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-6-luna
```

The architecture isolates the provider in `app/llm.py`, so the workflow executor does not depend on a particular model vendor.

## How each assignment workflow is mapped

| ID | Workflow | Main implementation |
|---|---|---|
| WF001 | Inventory Restock Check | inventory reader + threshold/reorder logic |
| WF002 | Product Price Validation | SKU matching + percentage difference |
| WF003 | Vendor File Processing | column normalization + validation |
| WF004 | Product Description Generator | LLM content generation + missing-data guard |
| WF005 | Customer Order Status | order lookup + shipment lookup + not-found handling |
| WF006 | Duplicate Product Detection | SKU/name/attribute similarity + confidence |
| WF007 | Marketing Campaign Brief | input validation + structured LLM content |
| WF008 | SEO Keyword Classification | deduplication + intent classification + page mapping |
| WF009 | Employee Task Assignment | skill/capacity ranking + escalation |
| WF010 | Workflow Performance Report | failure rate + execution time + error/slow-step analysis |

## 11th workflow scalability

The important design decision is that **workflow selection, API surface, tool registry, result model, logging format, and error handling are shared**.

For a new workflow:

1. Add its row to the Excel source.
2. Add or reuse the required tools.
3. Implement only the workflow-specific business handler.
4. The same `WorkflowAgent` and `/agent/run` endpoint automatically expose it.

There is no new chatbot, no new API endpoint, and no duplicated agent loop.

For workflows composed entirely from existing primitives, the handler can be reduced further by making the Excel step specification declarative.

## Evaluation / demo checklist

The Loom should demonstrate:

1. Show Excel `Workflows` sheet.
2. Show the reusable architecture.
3. Start the FastAPI app.
4. Run WF001 and show selected workflow + executed tools + result.
5. Run WF005 with `ORD-1001`.
6. Run WF005 with `ORD-9999` to demonstrate error handling.
7. Run WF004 and show generated content + missing attribute policy.
8. Run WF009 with a valid task and explain ranking.
9. Run `pytest -q` and show all tests passing.
10. Explain that adding WF011 uses the same agent/tool/API infrastructure.

## Design decisions

### Why not 10 separate agents?
Because the assignment explicitly asks for a reusable architecture. A single orchestrator avoids duplicated selection logic, error handling, API contracts, and tool registration.

### Why keep business logic deterministic?
The sample business systems are not provided. Deterministic local simulations make the submission reproducible and testable. LLMs are used where they add value: intent/workflow selection and natural-language generation.

### Why Pydantic?
It provides explicit contracts for workflow definitions and agent responses, which reduces malformed agent outputs.

### Why a tool registry?
Tools become replaceable adapters. A CSV reader can later be replaced by PostgreSQL, Shopify, an internal REST API, or another service without rewriting the agent.

## Security notes

- No real credentials are committed.
- `.env` is ignored.
- Sample data contains only synthetic records.
- External APIs are simulated unless the evaluator explicitly configures an LLM provider.
