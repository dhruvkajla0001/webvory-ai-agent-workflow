from __future__ import annotations

import json
import os
import re
from typing import Any

import requests

from .models import WorkflowSpec


class LLMProvider:
    def select_workflow(
        self,
        request: str,
        workflows: list[WorkflowSpec],
    ) -> tuple[str, str]:
        raise NotImplementedError

    def generate_product_content(
        self,
        product: dict[str, Any],
    ) -> dict[str, str]:
        raise NotImplementedError

    def generate_campaign_content(
        self,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        raise NotImplementedError


# ============================================================
# MOCK PROVIDER
# ============================================================

class MockLLMProvider(LLMProvider):
    """
    Deterministic local provider.

    Useful for:
    - Testing
    - CI/CD
    - Demo without an LLM
    - Offline execution
    """

    def select_workflow(
        self,
        request: str,
        workflows: list[WorkflowSpec],
    ) -> tuple[str, str]:

        text = request.lower()

        keyword_map = {
            "WF001": [
                "restock",
                "restocking",
                "low stock",
                "reorder",
                "inventory",
                "purchase more",
                "buy more",
            ],
            "WF002": [
                "price",
                "vendor price",
                "price difference",
                "validate price",
            ],
            "WF003": [
                "vendor file",
                "vendor spreadsheet",
                "process this file",
                "cleaned dataset",
            ],
            "WF004": [
                "description",
                "seo content",
                "product content",
                "product description",
            ],
            "WF005": [
                "order status",
                "where is order",
                "tracking",
                "shipment",
                "order ord",
            ],
            "WF006": [
                "duplicate",
                "duplicates",
                "similar products",
            ],
            "WF007": [
                "campaign brief",
                "marketing campaign",
                "campaign",
                "collection",
            ],
            "WF008": [
                "keyword",
                "keywords",
                "search intent",
                "seo keyword",
            ],
            "WF009": [
                "assign",
                "assignment",
                "best available",
                "employee task",
                "developer",
            ],
            "WF010": [
                "performance report",
                "failing",
                "failure rate",
                "execution logs",
                "slow workflows",
            ],
        }

        scores = {
            wid: sum(
                1
                for keyword in keywords
                if keyword in text
            )
            for wid, keywords in keyword_map.items()
        }

        best = max(
            scores,
            key=scores.get,
        )

        if scores[best] == 0:
            for wf in workflows:
                trigger_words = [
                    word
                    for word in wf.trigger.lower().split()
                    if len(word) > 3
                ]

                if any(
                    word in text
                    for word in trigger_words
                ):
                    return (
                        wf.workflow_id,
                        f"Matched trigger: {wf.trigger}",
                    )

            return (
                "",
                "No workflow matched the request.",
            )

        return (
            best,
            f"Matched request intent against workflow {best}.",
        )

    def generate_product_content(
        self,
        product: dict[str, Any],
    ) -> dict[str, str]:

        missing = product.get(
            "missing",
            [],
        )

        if missing:
            missing_text = ", ".join(missing)
            qualifier = (
                f"Missing information: {missing_text}."
            )
        else:
            qualifier = (
                "All supplied product attributes were used; "
                "no attributes were invented."
            )

        name = product.get(
            "product_name",
            "Unnamed product",
        )

        category = product.get(
            "category",
            "Product",
        )

        material = product.get("material")
        color = product.get("color")
        audience = product.get("target_audience")

        attributes = product.get(
            "attributes"
        ) or {}

        attr_text = ", ".join(
            f"{key}: {value}"
            for key, value in attributes.items()
        )

        description = (
            f"{name} is a {category.lower()} designed for "
            f"{audience or 'the target customer'}. "
            f"{'Made from ' + material + '. ' if material else ''}"
            f"{'Available in ' + color + '. ' if color else ''}"
            f"{'Key attributes include ' + attr_text + '. ' if attr_text else ''}"
            f"{qualifier}"
        )

        return {
            "description": description,
            "short_description": (
                f"{name} — {category}. {qualifier}"
            ),
            "seo_title": f"{name} | {category}",
            "meta_description": (
                f"Explore {name}. {qualifier}"
            ),
        }

    def generate_campaign_content(
        self,
        data: dict[str, Any],
    ) -> dict[str, Any]:

        products = data.get(
            "products",
            [],
        )

        goal = data["goal"]
        audience = data["audience"]

        promotion = data.get(
            "promotion",
            "standard offer",
        )

        dates = data["dates"]

        return {
            "objective": goal,
            "audience": audience,
            "products_summary": [
                p.get("name", p)
                if isinstance(p, dict)
                else p
                for p in products
            ],
            "messaging": [
                f"Lead with the {goal.lower()} benefit.",
                f"Promote {promotion} clearly.",
                (
                    f"Use customer language appropriate "
                    f"for {audience}."
                ),
            ],
            "channels": [
                "Email",
                "Instagram",
                "Paid social",
                "Website",
            ],
            "timeline": dates,
            "checklist": [
                "Approve creative",
                "Validate product/pricing data",
                "Schedule channels",
                "Launch campaign",
                "Review performance",
            ],
        }


# ============================================================
# OLLAMA / LLAMA 3.2 PROVIDER
# ============================================================

class OllamaProvider(LLMProvider):
    """
    Local LLM provider using Ollama.

    .env:

    LLM_PROVIDER=ollama
    OLLAMA_BASE_URL=http://127.0.0.1:11434
    OLLAMA_MODEL=llama3.2
    """

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
    ):

        self.base_url = (
            base_url
            or os.environ.get(
                "OLLAMA_BASE_URL",
                "http://127.0.0.1:11434",
            )
        ).rstrip("/")

        self.model = (
            model
            or os.environ.get(
                "OLLAMA_MODEL",
                "llama3.2",
            )
        )

    def _generate(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:

        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "system": system_prompt,
                "prompt": user_prompt,
                "stream": False,
                "format": "json",
            },
            timeout=120,
        )

        response.raise_for_status()

        data = response.json()

        return data.get(
            "response",
            "",
        ).strip()

    def _json(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> dict[str, Any]:

        raw = self._generate(
            system_prompt,
            user_prompt,
        )

        try:
            return json.loads(raw)

        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Ollama returned invalid JSON: {raw}"
            ) from exc

    def select_workflow(
        self,
        request: str,
        workflows: list[WorkflowSpec],
    ) -> tuple[str, str]:

        catalog = [
            {
                "workflow_id": workflow.workflow_id,
                "workflow_name": workflow.workflow_name,
                "trigger": workflow.trigger,
                "inputs": workflow.inputs,
                "steps": workflow.steps,
                "decision_logic": workflow.decision_logic,
            }
            for workflow in workflows
        ]

        system_prompt = """
You are the workflow classification agent for an AI
workflow automation system.

Select the ONE workflow that best matches the user's
actual business intent.

Rules:

1. Compare the complete user intent against ALL workflows.
2. Read workflow name, trigger, inputs, steps and
   decision logic.
3. Do not choose a workflow because of one weak keyword.
4. Prefer the workflow whose business purpose directly
   answers the request.
5. Never invent a workflow ID.
6. Return ONLY valid JSON.

IMPORTANT WORKFLOW DISTINCTIONS:

WF001 = Inventory Restock Check

Use WF001 when the user wants to:
- find products with low stock
- find products needing restocking
- know what products should be reordered
- know what products should be purchased more
- calculate reorder quantities
- identify products below minimum stock
- analyze current inventory levels

WF002 = Product Price Validation

Use WF002 when the user wants to:
- compare product prices
- validate selling prices
- compare vendor prices
- find pricing differences
- identify pricing problems

WF003 = Vendor File Processing

Use WF003 when the user wants to:
- process a vendor file
- process a vendor spreadsheet
- clean vendor data
- validate vendor data
- transform vendor records

WF004 = Product Description Generator

Use WF004 when the user wants to:
- generate product descriptions
- create product content
- generate SEO product copy
- create product titles
- create meta descriptions

WF005 = Customer Order Status

Use WF005 when the user wants to:
- check an order
- check order status
- find shipment information
- find tracking information
- know where an order is

WF006 = Duplicate Product Detection

Use WF006 when the user wants to:
- find duplicate products
- identify duplicate catalog entries
- find similar product records

WF007 = Marketing Campaign Brief

Use WF007 when the user wants to:
- create a marketing campaign
- create a campaign brief
- plan a promotional campaign
- create campaign messaging

WF008 = SEO Keyword Classification

Use WF008 when the user wants to:
- classify SEO keywords
- classify keywords
- determine search intent
- categorize keywords
- analyze keyword intent

WF009 = Employee Task Assignment

Use WF009 when the user wants to:
- assign a task
- assign work to an employee
- find the best available employee
- allocate work based on skills

WF010 = Workflow Performance Report

Use WF010 when the user wants to:
- analyze workflow execution
- generate a performance report
- identify slow workflows
- analyze failures
- analyze execution logs

CRITICAL EXAMPLES:

User:
"Which products need restocking?"

Answer:
WF001

User:
"Tell me which items I should purchase more of
based on their current inventory levels."

Answer:
WF001

User:
"Find duplicate products."

Answer:
WF006

User:
"Classify these SEO keywords."

Answer:
WF008

Do NOT select WF006 merely because the request
mentions products.

Do NOT select WF008 merely because the word
"items" or "products" appears.

For inventory purchasing/reordering requests,
WF001 is the correct workflow.

Return exactly:

{
  "workflow_id": "WF001",
  "reason": "Brief explanation."
}
"""

        user_prompt = json.dumps(
            {
                "user_request": request,
                "available_workflows": catalog,
            },
            indent=2,
        )

        data = self._json(
            system_prompt,
            user_prompt,
        )

        llm_workflow_id = str(
            data.get(
                "workflow_id",
                "",
            )
        ).strip()

        llm_reason = str(
            data.get(
                "reason",
                "Selected by Llama 3.2.",
            )
        ).strip()

        valid_ids = {
            workflow.workflow_id
            for workflow in workflows
        }

        if llm_workflow_id not in valid_ids:
            raise ValueError(
                f"Ollama selected invalid workflow: "
                f"{llm_workflow_id}"
            )

        # --------------------------------------------------------
        # HYBRID VALIDATION
        # --------------------------------------------------------
        #
        # Llama performs semantic classification.
        # This lightweight layer catches obvious mismatches.
        #
        # It is generic and uses the Excel workflow definitions.
        # It does not create ten separate chatbots.
        # --------------------------------------------------------

        def normalize(value: Any) -> set[str]:

            if value is None:
                return set()

            if isinstance(value, list):
                value = " ".join(
                    str(item)
                    for item in value
                )

            elif isinstance(value, dict):
                value = " ".join(
                    f"{key} {val}"
                    for key, val in value.items()
                )

            words = re.findall(
                r"[a-z0-9]+",
                str(value).lower(),
            )

            stop_words = {
                "the",
                "and",
                "for",
                "with",
                "from",
                "that",
                "this",
                "which",
                "what",
                "when",
                "where",
                "how",
                "are",
                "is",
                "to",
                "of",
                "a",
                "an",
                "in",
                "on",
                "or",
                "be",
                "by",
                "user",
                "request",
                "workflow",
            }

            return {
                word
                for word in words
                if len(word) >= 4
                and word not in stop_words
            }

        request_terms = normalize(request)

        def workflow_terms(
            workflow_data: dict[str, Any],
        ) -> set[str]:

            combined = " ".join(
                str(
                    workflow_data.get(
                        field,
                        "",
                    )
                )
                for field in (
                    "workflow_name",
                    "trigger",
                    "inputs",
                    "steps",
                    "decision_logic",
                )
            )

            return normalize(combined)

        term_sets = {
            item["workflow_id"]: workflow_terms(item)
            for item in catalog
        }

        overlap_scores = {
            workflow_id: len(
                request_terms & terms
            )
            for workflow_id, terms in term_sets.items()
        }

        selected_score = overlap_scores.get(
            llm_workflow_id,
            0,
        )

        best_id = max(
            overlap_scores,
            key=overlap_scores.get,
        )

        best_score = overlap_scores[best_id]

        # Only override Llama when:
        # 1. Another workflow has clear catalog overlap.
        # 2. Llama's selected workflow has zero overlap.
        #
        # This prevents unnecessary overrides.

        if (
            best_score > 0
            and selected_score == 0
            and best_id != llm_workflow_id
        ):

            return (
                best_id,
                (
                    f"Llama initially selected "
                    f"{llm_workflow_id}, but catalog "
                    f"validation matched the request "
                    f"more strongly to {best_id}."
                ),
            )

        return (
            llm_workflow_id,
            llm_reason,
        )

    def generate_product_content(
        self,
        product: dict[str, Any],
    ) -> dict[str, str]:

        system_prompt = """
You are an e-commerce content generation agent.

Generate product content ONLY from the supplied
product data.

Rules:
1. Never invent product attributes.
2. Do not invent material, color, size, features,
   or specifications.
3. If information is missing, clearly mention
   that it is missing.
4. Return ONLY valid JSON.

Required keys:

{
  "description": "...",
  "short_description": "...",
  "seo_title": "...",
  "meta_description": "..."
}
"""

        return self._json(
            system_prompt,
            json.dumps(
                product,
                indent=2,
            ),
        )

    def generate_campaign_content(
        self,
        data: dict[str, Any],
    ) -> dict[str, Any]:

        system_prompt = """
You are a marketing campaign planning agent.

Create a structured campaign brief using ONLY
the supplied data.

Rules:
1. Do not invent mandatory inputs.
2. Do not invent products.
3. Keep the campaign aligned with the supplied
   goal, audience, promotion, products and dates.
4. Return ONLY valid JSON.

Include:
- objective
- audience
- products_summary
- messaging
- channels
- timeline
- checklist
"""

        return self._json(
            system_prompt,
            json.dumps(
                data,
                indent=2,
            ),
        )


# ============================================================
# OPENAI PROVIDER
# ============================================================

class OpenAIProvider(LLMProvider):
    """
    Optional OpenAI provider.

    .env:

    LLM_PROVIDER=openai
    OPENAI_API_KEY=...
    OPENAI_MODEL=...
    """

    def __init__(
        self,
        model: str | None = None,
    ):

        from openai import OpenAI

        api_key = os.environ.get(
            "OPENAI_API_KEY"
        )

        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY is required "
                "for OpenAI provider."
            )

        self.client = OpenAI(
            api_key=api_key
        )

        self.model = (
            model
            or os.environ.get(
                "OPENAI_MODEL",
                "gpt-6-luna",
            )
        )

    def _json(
        self,
        response: Any,
    ) -> dict[str, Any]:

        text = getattr(
            response,
            "output_text",
            "",
        ).strip()

        if not text:
            raise ValueError(
                "OpenAI returned an empty response."
            )

        return json.loads(text)

    def select_workflow(
        self,
        request: str,
        workflows: list[WorkflowSpec],
    ) -> tuple[str, str]:

        catalog = [
            {
                "id": workflow.workflow_id,
                "name": workflow.workflow_name,
                "trigger": workflow.trigger,
                "inputs": workflow.inputs,
                "steps": workflow.steps,
                "decision_logic": workflow.decision_logic,
            }
            for workflow in workflows
        ]

        response = self.client.responses.create(
            model=self.model,
            input=[
                {
                    "role": "system",
                    "content": (
                        "Select exactly one workflow for "
                        "the user's request. "
                        "Compare the user's actual intent "
                        "against all available workflows. "
                        "Return only JSON: "
                        "{\"workflow_id\":\"WFxxx\","
                        "\"reason\":\"...\"}. "
                        "Never invent a workflow ID."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "request": request,
                            "workflows": catalog,
                        }
                    ),
                },
            ],
        )

        data = self._json(
            response
        )

        return (
            data["workflow_id"],
            data.get(
                "reason",
                "LLM selection",
            ),
        )

    def generate_product_content(
        self,
        product: dict[str, Any],
    ) -> dict[str, str]:

        response = self.client.responses.create(
            model=self.model,
            input=[
                {
                    "role": "system",
                    "content": (
                        "Generate e-commerce product "
                        "copy from supplied fields. "
                        "Never invent missing attributes. "
                        "Return JSON with keys: "
                        "description, "
                        "short_description, "
                        "seo_title, "
                        "meta_description."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        product
                    ),
                },
            ],
        )

        return self._json(
            response
        )

    def generate_campaign_content(
        self,
        data: dict[str, Any],
    ) -> dict[str, Any]:

        response = self.client.responses.create(
            model=self.model,
            input=[
                {
                    "role": "system",
                    "content": (
                        "Create a structured "
                        "marketing campaign brief "
                        "from supplied data. "
                        "Do not invent missing "
                        "mandatory inputs. "
                        "Return JSON."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        data
                    ),
                },
            ],
        )

        return self._json(
            response
        )


# ============================================================
# PROVIDER FACTORY
# ============================================================

def build_llm() -> LLMProvider:
    """
    Build the LLM provider from environment configuration.

    Supported modes:

    LLM_PROVIDER=mock
    LLM_PROVIDER=ollama
    LLM_PROVIDER=openai
    """

    provider = os.environ.get(
        "LLM_PROVIDER",
        "mock",
    ).lower().strip()

    # --------------------------------------------------------
    # MOCK
    # --------------------------------------------------------

    if provider == "mock":
        return MockLLMProvider()

    # --------------------------------------------------------
    # OLLAMA / LLAMA 3.2
    # --------------------------------------------------------

    if provider == "ollama":

        try:
            return OllamaProvider()

        except Exception as exc:

            print(
                "[WARNING] Ollama provider could not "
                f"be initialized: {exc}"
            )

            print(
                "[WARNING] Falling back to "
                "MockLLMProvider."
            )

            return MockLLMProvider()

    # --------------------------------------------------------
    # OPENAI
    # --------------------------------------------------------

    if provider == "openai":

        try:
            return OpenAIProvider()

        except Exception as exc:

            print(
                "[WARNING] OpenAI provider could not "
                f"be initialized: {exc}"
            )

            print(
                "[WARNING] Falling back to "
                "MockLLMProvider."
            )

            return MockLLMProvider()

    # --------------------------------------------------------
    # UNKNOWN PROVIDER
    # --------------------------------------------------------

    raise ValueError(
        f"Unsupported LLM_PROVIDER='{provider}'. "
        "Use 'mock', 'ollama', or 'openai'."
    )