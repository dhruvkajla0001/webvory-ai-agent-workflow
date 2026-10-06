# Architecture Notes

## Layers

### 1. Workflow definition layer
`excel_loader.py` converts the supplied workbook into typed `WorkflowSpec` objects.

### 2. Agent layer
`WorkflowAgent` is the only orchestrator. It receives natural language, selects a workflow, executes it and returns a structured result.

### 3. Tool layer
`ToolRegistry` is the common interface for business capabilities. `SimulatedTools` provides local implementations.

### 4. LLM layer
`LLMProvider` separates model-specific behavior from the agent. `MockLLMProvider` is deterministic. `OpenAIProvider` can be enabled through configuration.

### 5. Workflow logic
`WorkflowHandlers` contains business-specific decisions, while the orchestration contract remains identical for all workflows.

### 6. API layer
FastAPI exposes one `/agent/run` endpoint plus `/workflows` and `/health`.

## Why this is scalable

The architecture separates **what workflow exists** from **how requests are transported** and **how tools are implemented**. This prevents the common anti-pattern of making one chatbot class per business process.

The next architectural evolution would be to make more workflow steps declarative: Excel/JSON would specify tool names and typed arguments, while the executor interprets those definitions. This would reduce code changes for workflows composed from existing tools.
