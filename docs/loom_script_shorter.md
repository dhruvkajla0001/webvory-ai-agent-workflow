# Webvory AI Agent Workflow Automation — Loom Script

**Target duration: 5–6 minutes**

---

## 1. Opening — 20 seconds

**Screen:** Show GitHub repository / project folder.

**Say:**

> Hi, this is my solution for the Webvory AI Agent Workflow Automation assignment.
>
> I built one reusable AI agent architecture instead of creating ten separate chatbots.
>
> The system reads workflow definitions from Excel, understands the user's request using Llama 3.2, selects and validates the correct workflow, executes the required business logic and tools, and returns a structured result.

---

## 2. Excel Workflow Source — 30 seconds

**Screen:** Open:

```text
data/AI_Agent_Workflow_Assessment.xlsx
```

Open the `Workflows` sheet.

**Say:**

> This Excel file acts as the workflow catalog and source of truth.
>
> Each workflow contains its ID, trigger, inputs, steps, decision logic, required tools and expected output.
>
> I load these definitions dynamically using `excel_loader.py`, so the agent isn't hard-coded around ten individual conversations.

Briefly show WF001–WF010.

---

## 3. Architecture — 40 seconds

**Screen:** Open `docs/architecture.md` or your architecture diagram.

Point to:

```text
User Request
     ↓
WorkflowAgent
     ↓
LLM Workflow Selection
     ↓
Catalog Validation
     ↓
Workflow Handler
     ↓
ToolRegistry
     ↓
Business Logic
     ↓
Final Result
```

**Say:**

> The WorkflowAgent is the main orchestrator.
>
> The LLM handles natural-language understanding and workflow selection.
>
> After selection, I validate the workflow against the catalog because LLMs are probabilistic.
>
> The actual business operations are handled by deterministic workflow logic and reusable tools.
>
> This keeps the system flexible while making the business-critical operations predictable and testable.

---

## 4. LLM Layer — 25 seconds

**Screen:** Show `.env.example` or `app/llm.py`.

**Say:**

> For this demonstration I'm using Llama 3.2 locally through Ollama.
>
> I also implemented Mock and OpenAI providers, so the workflow architecture isn't tied to a single LLM provider.
>
> The LLM is mainly used for semantic workflow selection and content-generation tasks.

Show:

```env
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.2
```

---

# 5. Demo 1 — Inventory Restock — 40 seconds

**Run:**

```powershell
python -m app.cli --request "Tell me which items I should purchase more of based on their current inventory levels."
```

**Say:**

> Here I'm intentionally using natural language instead of the exact workflow name.
>
> The agent understands the request and selects WF001, Inventory Restock Check.
>
> The workflow then checks the inventory, compares stock against the configured thresholds and calculates the required reorder quantities.
>
> Notice that the LLM is not calculating the inventory values. The actual result comes from deterministic business logic and data.

Show the successful result.

---

# 6. Demo 2 — Duplicate Detection — 35 seconds

**Run:**

```powershell
python -m app.cli --request "Find products in the catalog that appear to be duplicates."
```

**Say:**

> This request is routed to WF006, Duplicate Product Detection.
>
> The workflow compares product names and attributes using similarity logic and groups likely duplicates with confidence information.

Show:

```text
SKU100 — UrbanTrail Backpack
SKU101 — Urban Trail Backpack

Confidence: high
```

Then briefly show the second duplicate group.

**Say:**

> Again, the LLM identifies the workflow, but the duplicate detection itself is performed by the workflow logic.

---

# 7. Demo 3 — Error Handling — 30 seconds

**Run:**

```powershell
python -m app.cli --request "Where is order ORD-9999?"
```

**Say:**

> Now I'm intentionally using an order that doesn't exist.
>
> Instead of fabricating an answer, the WF005 workflow follows its not-found condition and returns an appropriate error response.

Show the actual terminal result.

> This demonstrates that the workflow handles failure conditions rather than only the happy path.

---

# 8. Demo 4 — LLM Content Generation — 30 seconds

**Run:**

```powershell
python -m app.cli --request "Generate SEO content for this product."
```

**Say:**

> WF004 demonstrates where the LLM directly adds value.
>
> The workflow uses the LLM to generate product content such as the description, short description, SEO title and meta description.
>
> The workflow also applies validation around the available product information.

Show the generated result.

---

# 9. Show All 10 Workflows + Tests — 35 seconds

**Run:**

```powershell
python examples\run_all.py
```

**Say:**

> Although I'm only demonstrating a few workflows individually, the project contains all ten workflows from the assignment.
>
> This command runs examples across the complete workflow set.

Then run:

```powershell
pytest -q
```

Show:

```text
15 passed
```

**Say:**

> I also included automated tests covering all ten workflows and important error and decision paths. The current test suite has 15 passing tests.

---

# 10. Scalability / Workflow 11 — 35 seconds

**Screen:** Show Excel workflow catalog and `agent.py`.

**Say:**

> One of the key requirements was scalability.
>
> The shared agent, API layer, tool registry and orchestration logic do not need to be duplicated for every workflow.
>
> A new workflow can be added to the workflow catalog, with only the workflow-specific capability implemented when required.
>
> So the architecture is designed around one reusable agent rather than ten independent chatbots.

Then say:

> For workflows that can be composed entirely from existing tools, this architecture can be extended further toward fully declarative execution from the Excel definitions.

---

# 11. Quick Repository Overview — 20 seconds

**Screen:** Show repository.

Point to:

```text
app/
data/
examples/
tests/
docs/
README.md
requirements.txt
.env.example
```

**Say:**

> The repository contains the application code, Excel workflow definitions, synthetic business data, examples, automated tests and documentation required to reproduce the project.

---

# 12. Closing — 15 seconds

**Say:**

> So overall, the system combines LLM-based natural-language understanding with deterministic workflow execution.
>
> Excel provides the workflow definitions, the agent handles orchestration, reusable tools provide the required capabilities, and the business logic remains testable and predictable.
>
> Thank you for reviewing my solution.

---

# If They Ask Questions

### Why did you use an LLM?

> The LLM allows different natural-language requests to map to the same workflow without requiring users to know the exact workflow name.

### Why not let the LLM execute everything?

> I wanted business-critical operations to remain deterministic. The LLM handles understanding and generation, while actual business calculations and decisions are handled by tools and workflow logic.

### What happens if the LLM selects the wrong workflow?

> I added a catalog-validation layer after semantic selection. The selected workflow is checked against the workflow metadata before execution.

### How would you add Workflow 11?

> The shared agent, API, tool registry and orchestration remain unchanged. I would add the new workflow definition and implement only the workflow-specific capability required for it.

### Why Ollama?

> It allowed me to demonstrate a real Llama 3.2 model locally without requiring an external API key, while keeping the LLM provider isolated from the rest of the architecture.

### Why Excel?

> Excel was the format provided by the assignment, so I treated it as a configuration and workflow-definition layer rather than hard-coding the workflow metadata into the application.