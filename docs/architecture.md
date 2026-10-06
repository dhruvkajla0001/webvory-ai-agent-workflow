# Webvory – AI Agent Workflow Automation

A reusable Python agent architecture that converts the **10 workflows supplied in the Webvory Excel assignment** into executable, testable workflows.

## What this demonstrates

- Excel is the workflow source of truth.
- One reusable `WorkflowAgent` handles all workflow requests.
- The agent selects the correct workflow from the user's natural-language request.
- Llama 3.2 can perform semantic workflow selection through Ollama.
- A lightweight catalog-validation layer validates the LLM's workflow selection against the workflow metadata loaded from Excel.
- A shared `ToolRegistry` provides reusable tools such as CSV readers, calculators, validators, similarity, order lookup, and log readers.
- Each workflow produces an auditable execution trace: selected workflow → steps → tools → conditions → result.
- Business APIs are simulated with local CSV datasets so the project runs without external credentials.
- Multiple LLM providers are supported: Mock, Ollama, and OpenAI.
- Failure/condition handling is demonstrated for missing orders, missing campaign/task inputs, invalid vendor rows, and no suitable employee.
- Adding an 11th workflow does not require a new chatbot or API endpoint. The same agent, registry, executor, and tool layer are reused.

---

# Architecture

```text
                         User Request
                              │
                              ▼
                  ┌─────────────────────────┐
                  │     WorkflowAgent       │
                  │                         │
                  │ Natural-language        │
                  │ request orchestration   │
                  └────────────┬────────────┘
                               │
                               ▼
                  ┌─────────────────────────┐
                  │   Workflow Selection    │
                  │                         │
                  │ LLM semantic routing    │
                  │ + catalog validation    │
                  └────────────┬────────────┘
                               │
                               ▼
                  ┌─────────────────────────┐
                  │ Excel Workflow Registry │
                  │                         │
                  │ WF001 ... WF010         │
                  │                         │
                  │ Name                    │
                  │ Trigger                 │
                  │ Inputs                  │
                  │ Steps                   │
                  │ Decision Logic          │
                  │ Tools Required          │
                  └────────────┬────────────┘
                               │
                               ▼
                  ┌─────────────────────────┐
                  │ Workflow Handler        │
                  │                         │
                  │ WF-specific business    │
                  │ logic and decisions     │
                  └────────────┬────────────┘
                               │
                  ┌────────────┴────────────┐
                  ▼                         ▼
       ┌────────────────────┐    ┌────────────────────┐
       │    ToolRegistry    │    │    LLM Provider    │
       │                    │    │                    │
       │ CSV readers        │    │ Mock               │
       │ calculators        │    │ Ollama / Llama 3.2 │
       │ validators         │    │ OpenAI             │
       │ similarity         │    │                    │
       │ order lookup       │    └────────────────────┘
       │ log readers        │
       └──────────┬─────────┘
                  │
                  ▼
       ┌────────────────────────┐
       │ Conditions / Errors    │
       │                        │
       │ Validation             │
       │ Missing inputs         │
       │ Not-found cases        │
       │ Business thresholds    │
       │ Escalation             │
       └────────────┬───────────┘
                    │
                    ▼
       ┌────────────────────────┐
       │ Auditable Agent Result │
       │                        │
       │ Selected workflow      │
       │ Selection reason       │
       │ Executed steps        │
       │ Tools used             │
       │ Final result           │
       │ Errors / conditions    │
       └────────────────────────┘
```

---

# 1. Workflow Definition Layer

`excel_loader.py` converts the supplied workbook into typed `WorkflowSpec` objects.

The Excel workbook contains the workflow catalog, including:

- Workflow ID
- Workflow Name
- Trigger
- Inputs
- Steps
- Decision Logic
- Tools Required
- Expected Output

This makes Excel the source of truth for the available workflow catalog.

The agent does not need a separate chatbot for each workflow.

The workflow definitions are loaded into memory and supplied to the selection layer.

---

# 2. Agent Layer

`WorkflowAgent` is the main orchestrator.

It receives:

```text
User Request
+
Optional Context
```

and performs:

```text
1. Load available workflows
2. Select the best matching workflow
3. Validate the workflow selection
4. Execute the selected workflow
5. Capture execution steps
6. Return structured result
```

The same orchestration flow is reused for every workflow.

---

# 3. Workflow Selection Layer

The selection layer supports both deterministic and LLM-backed routing.

## LLM semantic routing

With:

```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=llama3.2
```

Llama 3.2 running locally through Ollama performs semantic workflow classification.

For example:

```text
User:
"Tell me which items I should purchase more of based on their current inventory levels."

             ↓

Llama 3.2

             ↓

WF001 - Inventory Restock Check
```

The model is given the available workflow catalog and is instructed to select the workflow whose business purpose best matches the request.

## Catalog validation layer

LLM classification is followed by a lightweight validation layer.

The validation layer compares the request against workflow metadata such as:

- workflow name
- trigger
- inputs
- steps
- decision logic

This provides a deterministic safety layer around the LLM decision.

The design therefore separates:

```text
Semantic understanding
        ↓
LLM classification
        ↓
Catalog validation
        ↓
Workflow execution
```

This prevents an obviously incorrect LLM classification from immediately triggering an unrelated business workflow.

---

# 4. LLM Provider Layer

`app/llm.py` isolates model-specific behavior from the workflow agent.

The application supports three providers.

## Mock provider

```env
LLM_PROVIDER=mock
```

The Mock provider is deterministic and useful for:

- automated tests
- offline execution
- reproducible demonstrations

## Ollama provider

```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=llama3.2
```

The current development configuration uses:

```text
Llama 3.2
      ↓
Ollama
      ↓
Local HTTP API
      ↓
OllamaProvider
```

This allows the project to demonstrate a real local LLM without requiring a cloud API key.

## OpenAI provider

OpenAI can also be configured through environment variables.

The provider abstraction means the workflow layer does not need to know which model provider is being used.

---

# 5. Tool Layer

`ToolRegistry` provides a common interface for reusable business capabilities.

Examples include:

```text
inventory_reader
price_reader
csv_reader
catalog_reader
keyword_reader
order_lookup
shipment_lookup
calculator
text_similarity
duplicate_grouper
employee_reader
log_reader
```

Tools are intentionally separated from workflow orchestration.

This makes it possible to replace simulated tools later with production integrations.

For example:

```text
Current:

CSV inventory
     ↓
inventory_reader

Possible production version:

PostgreSQL / Shopify API
     ↓
inventory_reader
```

The workflow agent would not need to change.

---

# 6. Simulated Business Systems

The assignment does not provide production APIs or databases.

Therefore, the project uses local synthetic CSV data to simulate business systems.

Examples:

```text
data/inventory.csv
data/product_prices.csv
data/vendor_prices.csv
data/vendor_products.csv
data/orders.csv
data/catalog.csv
data/keywords.csv
data/employees.csv
data/execution_logs.csv
```

This keeps the application:

- reproducible
- offline-capable
- testable
- free from external credentials

The simulated tools expose the same conceptual interface that could later be backed by real APIs or databases.

---

# 7. Workflow Logic Layer

`workflows.py` contains the workflow-specific business handlers.

The orchestration contract remains the same for every workflow:

```text
Request
   ↓
Workflow selection
   ↓
Workflow handler
   ↓
Tools
   ↓
Business conditions
   ↓
Structured result
```

The ten assignment workflows are mapped as follows:

| ID | Workflow | Main implementation |
|---|---|---|
| WF001 | Inventory Restock Check | Inventory reader + threshold/reorder logic |
| WF002 | Product Price Validation | SKU matching + percentage difference |
| WF003 | Vendor File Processing | Column normalization + validation |
| WF004 | Product Description Generator | LLM content generation + missing-data guard |
| WF005 | Customer Order Status | Order lookup + shipment lookup + not-found handling |
| WF006 | Duplicate Product Detection | SKU/name/attribute similarity + confidence |
| WF007 | Marketing Campaign Brief | Input validation + structured LLM content |
| WF008 | SEO Keyword Classification | Deduplication + intent classification + page mapping |
| WF009 | Employee Task Assignment | Skill/capacity ranking + escalation |
| WF010 | Workflow Performance Report | Failure rate + execution time + error/slow-step analysis |

---

# 8. Conditions and Error Handling

Business conditions are handled explicitly instead of allowing the LLM to invent business results.

Examples include:

### WF001

```text
current_stock < minimum_stock
        ↓
requires restock
        ↓
calculate reorder quantity
```

### WF002

```text
price difference > 10%
        ↓
flag exception
```

### WF003

```text
required field missing
        ↓
invalid row
```

### WF005

```text
order exists
        ↓
return order + shipment information

order does not exist
        ↓
return not-found/follow-up result
```

### WF009

```text
suitable employee exists
        ↓
rank candidates

no suitable employee
        ↓
escalation
```

This keeps business decisions deterministic and auditable.

---

# 9. API Layer

FastAPI exposes a single reusable agent endpoint:

```text
POST /agent/run
```

Additional endpoints:

```text
GET /health
GET /workflows
```

Example request:

```json
{
  "request": "Which products need restocking?",
  "context": {}
}
```

The response contains:

- selected workflow
- selection reason
- execution status
- executed steps
- tools used
- final result
- errors or follow-up information where applicable

The API surface does not grow when new workflows are added.

---

# 10. Pydantic Contracts

`models.py` contains typed contracts for workflow definitions and agent responses.

Pydantic provides:

- validation
- structured data contracts
- predictable API responses
- protection against malformed data
- clearer interfaces between components

This is particularly useful when LLM-generated information is involved.

---

# 11. Project Structure

```text
webvory_ai_agent_workflow/
│
├── app/
│   ├── __init__.py
│   ├── agent.py              # Reusable workflow agent
│   ├── cli.py                # Command-line interface
│   ├── excel_loader.py       # Excel → workflow registry
│   ├── llm.py                # Mock + Ollama + OpenAI providers
│   ├── main.py               # FastAPI application
│   ├── models.py             # Pydantic contracts
│   ├── workflows.py          # WF001–WF010 handlers
│   │
│   └── tools/
│       ├── __init__.py
│       ├── builtins.py       # Tool registration
│       ├── registry.py       # Shared tool registry
│       └── simulated.py      # Local business/API simulations
│
├── data/
│   ├── AI_Agent_Workflow_Assessment.xlsx
│   └── *.csv
│
├── examples/
│   ├── __init__.py
│   ├── requests.json
│   └── run_all.py
│
├── tests/
│   ├── __init__.py
│   └── test_workflows.py
│
├── docs/
│   ├── architecture.md
│   └── loom_script.md
│
├── outputs/
│
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

---

# 12. Setup

## Create environment

```bash
python -m venv .venv
```

### Windows

```powershell
.venv\Scripts\activate
```

### Linux/macOS

```bash
source .venv/bin/activate
```

## Install dependencies

```bash
pip install -r requirements.txt
```

---

# 13. Run Tests

```bash
pytest -q
```

The project currently includes automated tests covering all ten workflows, failure conditions, and data-driven workflow selection.

The current test suite contains 15 tests.

---

# 14. Run the CLI

Example:

```bash
python -m app.cli --request "Which products need restocking?"
```

Example:

```bash
python -m app.cli --request "Where is order ORD-1001?"
```

Campaign example:

```bash
python -m app.cli --request "Create a campaign brief for the new collection." --context "{\"goal\":\"Increase launch sales\",\"audience\":\"urban professionals\",\"promotion\":\"15% launch discount\",\"dates\":\"Oct 10-Oct 20\"}"
```

Run all ten assignment examples:

```bash
python examples/run_all.py
```

---

# 15. Run the Web Application

```bash
uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/docs
```

Use:

```text
POST /agent/run
```

---

# 16. 11th Workflow Scalability

The key architectural decision is that:

- workflow selection is shared
- the API surface is shared
- the agent loop is shared
- the tool registry is shared
- the response model is shared
- error handling is shared
- logging is shared

Therefore, adding workflow 11 does not require a new chatbot or API endpoint.

For a new workflow:

```text
1. Add workflow definition to Excel
        ↓
2. Add/reuse required tools
        ↓
3. Implement workflow-specific handler
        ↓
4. Existing WorkflowAgent executes it
        ↓
5. Existing /agent/run endpoint exposes it
```

For workflows composed entirely from existing primitives, the next architectural improvement would be to make the Excel workflow steps declarative.

For example:

```text
Excel:

Step 1 → inventory_reader
Step 2 → calculator
Step 3 → validator
Step 4 → result_builder
```

The generic executor could then interpret these steps directly.

This would reduce or eliminate workflow-specific Python handlers for workflows that only compose existing tools.

---

# 17. Testing Strategy

Testing covers both successful workflows and failure/condition paths.

Examples include:

```text
WF001 restock
WF002 price exceptions
WF003 invalid vendor rows
WF004 content generation
WF005 successful order
WF005 missing order
WF006 duplicate detection
WF007 missing campaign inputs
WF007 successful campaign
WF008 keyword classification
WF009 employee assignment
WF009 escalation
WF010 performance report
```

A data-driven workflow-selection test also verifies that the selection layer is not hard-coded to exactly ten workflows.

---

# 18. Design Decisions

## Why not ten separate agents?

The assignment asks for a reusable architecture.

Ten independent agents would duplicate:

- routing logic
- tool registration
- API endpoints
- response contracts
- error handling
- testing infrastructure

A single reusable agent avoids this duplication.

## Why use an LLM?

Natural-language requests can express the same business intent in many ways.

For example:

```text
"Which products need restocking?"

"Which items should I purchase more of?"

"Show me products below their inventory threshold."
```

These should all resolve to:

```text
WF001
```

Llama 3.2 provides semantic understanding for this routing problem.

## Why validate the LLM decision?

LLMs are probabilistic.

Business workflow execution should be more deterministic.

Therefore:

```text
LLM
 ↓
semantic classification
 ↓
catalog validation
 ↓
business workflow
```

provides a balance between natural-language flexibility and predictable execution.

## Why keep business logic deterministic?

The sample business systems are simulated.

The system should not allow an LLM to invent:

- inventory levels
- prices
- shipment status
- employee capacity
- execution metrics

These values come from tools and deterministic business rules.

## Why use a ToolRegistry?

Tools become replaceable adapters.

A simulated CSV reader can later be replaced by:

```text
PostgreSQL
Shopify
REST API
Internal service
Cloud database
```

without rewriting the agent architecture.

## Why Pydantic?

Pydantic provides explicit contracts between:

```text
Excel loader
      ↓
Agent
      ↓
Workflow handlers
      ↓
API response
```

This makes the system easier to validate and test.

---

# 19. Security

- No real credentials are committed.
- `.env` is ignored by Git.
- `.env.example` contains configuration placeholders.
- Sample business data is synthetic.
- External business APIs are simulated.
- Ollama can run locally without sending workflow data to a cloud model.
- OpenAI mode requires the evaluator to provide its own API key.

---

# 20. Demo Checklist

The Loom demonstration should show:

1. Open the Excel `Workflows` sheet.
2. Explain the workflow definition columns.
3. Show the architecture.
4. Explain `WorkflowAgent`.
5. Explain Llama 3.2 + Ollama workflow selection.
6. Explain the catalog validation layer.
7. Run WF001.
8. Run WF005 with `ORD-1001`.
9. Run WF005 with a missing order.
10. Run WF006 duplicate detection.
11. Run WF004 content generation.
12. Run WF009 employee assignment.
13. Run `pytest -q`.
14. Show the 11th-workflow scalability test/design.
15. Explain how simulated tools can be replaced by production APIs.

---

# 21. Summary

The system separates five major concerns:

```text
Workflow Definition
        ↓
Workflow Selection
        ↓
Workflow Orchestration
        ↓
Reusable Tools
        ↓
Business Logic + Conditions
```

The LLM is used where it provides value—natural-language understanding and content generation—while business-critical operations remain deterministic and tool-driven.

The resulting architecture is reusable, testable, provider-independent and designed to scale beyond the ten workflows supplied in the Webvory assignment.