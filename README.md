# Webvory – AI Agent Workflow Automation

A reusable Python AI-agent architecture for executing the **10 business workflows provided in the Webvory technical assignment**.

The system accepts a natural-language request, identifies the appropriate workflow, validates the selection, executes the workflow using reusable tools, handles business conditions/errors, and returns a structured execution result.

The architecture is designed so that workflows share the same agent, tools, API surface and orchestration infrastructure instead of becoming ten separate chatbots.

---

# Architecture

```text
User Request
     │
     ▼
WorkflowAgent
     │
     ▼
LLM Workflow Selection
(Llama 3.2 / Ollama)
     │
     ▼
Catalog Validation
     │
     ▼
Excel Workflow Registry
     │
     ▼
Workflow Handler
     │
     ├───────────────┐
     ▼               ▼
ToolRegistry     LLM Provider
     │           Mock / Ollama / OpenAI
     ▼
Business Conditions
     │
     ▼
Auditable Result
```

### Main design principle

The system separates:

1. **Workflow definitions**
2. **Natural-language workflow selection**
3. **Workflow orchestration**
4. **Reusable tools**
5. **Business logic and conditions**
6. **LLM providers**
7. **API transport**

This allows the architecture to scale without creating one agent or API endpoint per workflow.

---

# What This Demonstrates

- Excel-driven workflow definitions.
- Natural-language workflow selection.
- Llama 3.2 integration through Ollama.
- Deterministic catalog validation after LLM classification.
- One reusable `WorkflowAgent`.
- Shared `ToolRegistry`.
- Simulated business APIs using local CSV data.
- Structured Pydantic contracts.
- Workflow-specific business conditions.
- Error and missing-input handling.
- Automated tests.
- FastAPI exposure.
- Data-driven workflow scalability.

---

# Workflows

The supplied Excel workbook contains the following workflows:

| ID | Workflow | Purpose |
|---|---|---|
| WF001 | Inventory Restock Check | Identify low-stock products and calculate reorder quantities |
| WF002 | Product Price Validation | Compare product and vendor prices |
| WF003 | Vendor File Processing | Validate and clean vendor records |
| WF004 | Product Description Generator | Generate product/SEO content |
| WF005 | Customer Order Status | Retrieve order and shipment information |
| WF006 | Duplicate Product Detection | Identify similar/duplicate catalog records |
| WF007 | Marketing Campaign Brief | Generate a structured campaign brief |
| WF008 | SEO Keyword Classification | Classify search intent and map keywords to pages |
| WF009 | Employee Task Assignment | Rank available employees for a task |
| WF010 | Workflow Performance Report | Analyze failures and execution performance |

---

# Project Structure

```text
webvory_ai_agent_workflow/
│
├── app/
│   ├── agent.py              # Reusable workflow orchestrator
│   ├── cli.py                # CLI interface
│   ├── excel_loader.py       # Excel → WorkflowSpec loader
│   ├── llm.py                # Mock / Ollama / OpenAI providers
│   ├── main.py               # FastAPI application
│   ├── models.py             # Pydantic models
│   ├── workflows.py          # WF001–WF010 handlers
│   │
│   └── tools/
│       ├── builtins.py       # Tool registration
│       ├── registry.py       # Shared tool registry
│       └── simulated.py      # Local business/API simulations
│
├── data/
│   ├── AI_Agent_Workflow_Assessment.xlsx
│   └── *.csv
│
├── examples/
│   ├── requests.json
│   └── run_all.py
│
├── tests/
│   └── test_workflows.py
│
├── docs/
│   ├── architecture.md
│   └── loom_script.md
│
├── outputs/
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

---

# How It Works

## 1. Excel Workflow Registry

The supplied workbook is read by:

```text
app/excel_loader.py
```

The workflow definitions are converted into typed `WorkflowSpec` objects.

The workflow catalog contains:

```text
Workflow ID
Workflow Name
Trigger
Inputs
Steps
Decision Logic
Tools Required
Expected Output
```

This keeps workflow definitions separate from the orchestration code.

---

# 2. WorkflowAgent

`app/agent.py` contains the reusable agent.

The basic flow is:

```text
User Request
     ↓
Load Workflow Catalog
     ↓
Select Workflow
     ↓
Validate Selection
     ↓
Execute Workflow
     ↓
Return Structured Result
```

The same agent is reused for all ten workflows.

---

# 3. LLM Workflow Selection

The application supports three LLM modes:

### Mock

```env
LLM_PROVIDER=mock
```

Deterministic and useful for offline testing.

### Ollama / Llama 3.2

```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=llama3.2
```

This is the current demonstration configuration.

### OpenAI

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=your_model_here
```

The exact model can be configured through the environment.

---

# Why Use Llama for Workflow Selection?

The same business intent can be expressed in many ways.

For example:

```text
"Which products need restocking?"

"Which items should I purchase more of?"

"Show me products below their inventory threshold."
```

These requests should all map to:

```text
WF001 - Inventory Restock Check
```

Llama 3.2 provides semantic understanding rather than relying only on exact string matching.

---

# Catalog Validation

LLM output is not directly trusted for business execution.

After the LLM selects a workflow, a lightweight validation layer compares the request with workflow metadata:

```text
Workflow Name
Trigger
Inputs
Steps
Decision Logic
```

The flow is:

```text
Natural-language request
        ↓
Llama 3.2
        ↓
Semantic workflow selection
        ↓
Catalog validation
        ↓
Workflow execution
```

This combines the flexibility of an LLM with deterministic business safeguards.

---

# Tool Registry

`app/tools/registry.py` provides the shared tool interface.

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

Tools are separated from workflow orchestration so that simulated implementations can later be replaced with production systems.

For example:

```text
Current:
CSV → inventory_reader

Future:
PostgreSQL / Shopify API → inventory_reader
```

The agent architecture does not need to change.

---

# Simulated Business Data

The assignment does not provide production business APIs.

Therefore, local synthetic data is included:

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

This makes the application reproducible without external credentials.

---

# Setup

## 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd webvory-ai-agent-workflow
```

## 2. Create virtual environment

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

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

# Configure LLM

Copy:

```text
.env.example
```

to:

```text
.env
```

For local Llama 3.2:

```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=llama3.2
```

Make sure Ollama is installed and the model is available:

```bash
ollama pull llama3.2
```

If Ollama is already running, no additional `ollama serve` command is required.

---

# Run Tests

```bash
pytest -q
```

The test suite covers:

- all ten workflow implementations
- successful execution
- missing inputs
- missing orders
- invalid vendor rows
- duplicate detection
- employee escalation
- performance reporting
- data-driven workflow selection

Current test suite:

```text
15 passed
```

---

# Run All Workflow Examples

```bash
python examples/run_all.py
```

This executes the supplied workflow examples and displays:

```text
Selected workflow
Status
Final result
```

---

# CLI Examples

## WF001 — Inventory Restock

```bash
python -m app.cli --request "Which products need restocking?"
```

Natural-language variation:

```bash
python -m app.cli --request "Tell me which items I should purchase more of based on their current inventory levels."
```

---

## WF002 — Price Validation

```bash
python -m app.cli --request "Check whether our product prices are valid compared with vendor prices."
```

---

## WF003 — Vendor File Processing

```bash
python -m app.cli --request "Process this vendor spreadsheet and show invalid rows."
```

---

## WF004 — Product Description Generation

```bash
python -m app.cli --request "Generate SEO content for this product."
```

---

## WF005 — Order Status

```bash
python -m app.cli --request "Where is order ORD-1001?"
```

Missing order:

```bash
python -m app.cli --request "Where is order ORD-9999?"
```

---

## WF006 — Duplicate Detection

```bash
python -m app.cli --request "Find products in the catalog that appear to be duplicates."
```

---

## WF007 — Campaign Brief

```bash
python -m app.cli --request "Create a campaign brief for the new collection." --context "{\"goal\":\"Increase launch sales\",\"audience\":\"urban professionals\",\"promotion\":\"15% launch discount\",\"dates\":\"Oct 10-Oct 20\"}"
```

---

## WF008 — SEO Classification

```bash
python -m app.cli --request "Classify these keywords according to their SEO intent."
```

---

## WF009 — Employee Assignment

```bash
python -m app.cli --request "Assign this urgent task to the best available developer."
```

---

## WF010 — Performance Report

```bash
python -m app.cli --request "Which workflows are failing most often?"
```

---

# FastAPI

Start the application:

```bash
uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/docs
```

Main endpoint:

```text
POST /agent/run
```

Example:

```json
{
  "request": "Which products need restocking?",
  "context": {}
}
```

The response contains:

```text
selected workflow
selection reason
status
executed steps
tools used
final result
errors/follow-up information
```

Additional endpoints:

```text
GET /health
GET /workflows
```

---

# Error and Condition Handling

The implementation intentionally keeps important business decisions deterministic.

Examples:

### WF001

```text
current_stock < minimum_stock
        ↓
restock required
        ↓
calculate reorder quantity
```

### WF002

```text
price difference > 10%
        ↓
pricing exception
```

### WF003

```text
required field missing
        ↓
invalid vendor row
```

### WF005

```text
order found
        ↓
return shipment information

order missing
        ↓
return not-found/follow-up result
```

### WF009

```text
qualified employee available
        ↓
rank candidates

no suitable employee
        ↓
escalate
```

---

# Scalability: Adding Workflow 11

The architecture is intentionally not implemented as ten independent chatbots.

The following components are shared:

```text
WorkflowAgent
Workflow selector
Catalog validation
ToolRegistry
Pydantic response model
FastAPI endpoint
Error-handling structure
Logging/result structure
```

A new workflow can therefore follow:

```text
1. Add workflow definition
        ↓
2. Add/reuse required tools
        ↓
3. Implement workflow-specific logic if required
        ↓
4. Existing WorkflowAgent handles it
        ↓
5. Existing /agent/run endpoint exposes it
```

There is no need to create:

```text
New chatbot
New API endpoint
New orchestration loop
New tool registry
```

For workflows composed entirely from existing tools, a future enhancement would be to make the Excel step definitions declarative so the generic executor can interpret them directly.

---

# Testing Architecture

The test suite includes:

```text
test_all_ten_workflows_loaded
test_wf001_restock
test_wf002_price_exceptions
test_wf003_invalid_rows
test_wf004_generation
test_wf005_order
test_wf005_missing_order
test_wf006_duplicates
test_wf007_missing_inputs
test_wf007_success
test_wf008_keywords
test_wf009_assignment
test_wf009_escalation
test_wf010_report
test_new_workflow_is_data_driven_at_selection_layer
```

This gives coverage across both successful workflows and failure/condition paths.

---

# Design Decisions

## Why one reusable agent?

Ten separate agents would duplicate routing, tool registration, error handling and API contracts.

A single `WorkflowAgent` keeps the architecture reusable.

## Why use an LLM?

Users can express the same workflow intent using different language.

The LLM provides semantic workflow selection.

## Why not let the LLM execute the business logic?

Business-critical values such as inventory, pricing, shipment status and employee capacity should come from tools and deterministic rules.

The LLM is therefore used where it adds value without becoming the source of truth for business data.

## Why use catalog validation?

LLMs are probabilistic.

The validation layer provides a deterministic check before the selected workflow is executed.

## Why Ollama?

Ollama allows Llama 3.2 to run locally without requiring an external cloud API.

The provider abstraction also makes the application independent of a specific model provider.

## Why Pydantic?

Pydantic provides explicit contracts for workflow definitions and agent responses.

## Why a ToolRegistry?

The ToolRegistry makes business capabilities replaceable.

A local CSV implementation can later be replaced with a database or production API without changing the agent architecture.

---

# Security

- `.env` is excluded from Git.
- No real credentials are committed.
- `.env.example` contains placeholders only.
- Business datasets are synthetic.
- External business APIs are simulated.
- Ollama can run locally.
- OpenAI mode requires the evaluator to supply their own API key.

---

# Demo

The recommended Loom flow is:

1. Show the Excel workflow catalog.
2. Explain the architecture.
3. Show Llama 3.2 + Ollama configuration.
4. Demonstrate semantic workflow selection.
5. Run WF001.
6. Run WF002.
7. Run WF005 success and failure.
8. Run WF006 duplicate detection.
9. Run WF004 content generation.
10. Run WF009 employee assignment.
11. Show FastAPI `/docs`.
12. Run `pytest -q`.
13. Explain workflow 11 scalability.
14. Show repository structure.

See:

```text
docs/loom_script.md
```

for the complete demonstration script.

---

# Summary

This project implements the Webvory assignment as a reusable AI-agent architecture rather than ten separate chatbots.

The core design is:

```text
Excel Workflow Definitions
          ↓
Llama 3.2 Semantic Selection
          ↓
Catalog Validation
          ↓
Reusable WorkflowAgent
          ↓
Shared ToolRegistry
          ↓
Deterministic Business Logic
          ↓
Structured / Auditable Result
```

The architecture separates LLM capabilities from business-critical execution, making the system easier to test, maintain, replace and scale.