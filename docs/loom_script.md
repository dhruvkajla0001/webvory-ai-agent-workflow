# Loom Demonstration Script

Target length: 7–10 minutes.

## 1. Opening — 30 seconds

"Hi, this is my solution for the Webvory AI Agent Workflow Automation assignment. The main design goal was to avoid building ten separate chatbots. Instead, I built one reusable agent architecture where the Excel file acts as the workflow registry."

## 2. Excel source — 45 seconds

Open `data/AI_Agent_Workflow_Assessment.xlsx`.

Say:

"The Workflows sheet contains workflow ID, trigger, inputs, steps, decision logic, tools and expected output. My application reads this sheet at startup, so the workflow catalog is data-driven rather than duplicated in the API layer."

Show the 10 workflow rows.

## 3. Architecture — 1 minute

Open README architecture.

Explain:

"Every request enters the same WorkflowAgent. The selection layer identifies a workflow. The executor invokes reusable tools through a ToolRegistry. Conditions are implemented inside the workflow handler, and the response includes an execution trace."

Point out:

- Excel loader
- WorkflowAgent
- ToolRegistry
- simulated tools
- LLM provider
- Pydantic result contract

## 4. Working example — WF001 — 1 minute

Run:

```bash
python -m app.cli --request "Which products need restocking?"
```

Explain:

"The agent selected WF001, loaded inventory, compared current stock with minimum stock, calculated reorder quantities and returned the restock list."

## 5. Error handling — WF005 — 1 minute

Run:

```bash
python -m app.cli --request "Where is order ORD-1001?"
```

Then:

```bash
python -m app.cli --request "Where is order ORD-9999?"
```

Say:

"The first request returns shipment information. The second does not fabricate an answer; it asks for another identifier, matching the Excel decision logic."

## 6. LLM workflow — WF004 — 1 minute

Run:

```bash
python -m app.cli --request "Generate SEO content for this product."
```

Explain:

"The content-generation workflow is provider-independent. Mock mode makes the demo reproducible, while an OpenAI provider can be enabled through environment configuration."

## 7. Tool calling / ranking — WF009 — 1 minute

Use the example context from README.

Explain:

"The agent calls the employee database tool, scores candidates using required skills and available capacity, then returns the recommendation and reasoning."

## 8. Tests — 45 seconds

Run:

```bash
pytest -q
```

Say:

"I included happy paths for all ten workflows and failure paths for missing orders, missing campaign inputs and no suitable employee."

## 9. 11th workflow — 1 minute

Show `app/agent.py` and README.

Say:

"The API and agent loop are not duplicated per workflow. A new workflow uses the same request model, selector, tool registry, executor and response contract. Only workflow-specific logic and/or reusable tools need to be added."

## 10. Closing — 30 seconds

"The final architecture separates workflow definition, orchestration, tools, LLM capabilities and business logic. This makes it easier to test, maintain and replace simulated APIs with production integrations."
