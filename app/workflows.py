from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import Any

from .llm import LLMProvider
from .models import AgentResult, ExecutionStep, WorkflowSpec
from .tools.registry import ToolRegistry
from .tools.simulated import SimulatedTools


class WorkflowHandlers:
    def __init__(self, tools: ToolRegistry, data_dir: str, llm: LLMProvider):
        self.tools = tools
        self.data = SimulatedTools(data_dir)
        self.llm = llm

    def run(self, workflow_id: str, request: str, context: dict[str, Any] | None = None) -> AgentResult:
        context = context or {}
        fn = getattr(self, f"run_{workflow_id.lower()}", None)
        if not fn:
            return AgentResult(
                request=request,
                selected_workflow_id=workflow_id,
                status="failed",
                errors=[f"No handler registered for {workflow_id}"],
            )
        try:
            return fn(request, context)
        except Exception as exc:
            return AgentResult(
                request=request,
                selected_workflow_id=workflow_id,
                status="failed",
                errors=[f"{type(exc).__name__}: {exc}"],
            )

    def _step(self, n: int, action: str, tool: str | None = None, detail: str = ""):
        return ExecutionStep(step=n, action=action, tool=tool, detail=detail)

    def run_wf001(self, request, context):
        rows = self.tools.call("inventory_reader")
        restock = []
        for r in rows:
            if r["current_stock"] < r["minimum_stock"]:
                reorder = r["minimum_stock"] - r["current_stock"]
                restock.append({
                    "sku": r["sku"], "product": r["product"],
                    "current_stock": r["current_stock"],
                    "minimum_stock": r["minimum_stock"],
                    "suggested_reorder_quantity": reorder,
                })
        return AgentResult(
            request=request, selected_workflow_id="WF001",
            status="success",
            steps_executed=[
                self._step(1, "Load inventory", "inventory_reader", f"{len(rows)} products loaded"),
                self._step(2, "Compare current stock with minimum threshold", "calculator"),
                self._step(3, "Identify low-stock products", detail=f"{len(restock)} products below threshold"),
                self._step(4, "Calculate reorder quantity and generate restock list", "calculator"),
            ],
            result={"products_requiring_restock": restock},
        )

    def run_wf002(self, request, context):
        products, vendor = self.tools.call("price_reader")
        vendor_by_sku = {r["sku"]: float(r["vendor_price"]) for r in vendor}
        report = []
        for p in products:
            sku = p["sku"]
            if sku not in vendor_by_sku:
                report.append({"sku": sku, "status": "unmatched"})
                continue
            internal = float(p["internal_price"])
            vp = vendor_by_sku[sku]
            diff = abs(internal - vp) / vp * 100 if vp else 0
            report.append({
                "sku": sku, "internal_price": internal, "vendor_price": vp,
                "difference_percent": round(diff, 2),
                "exception": diff > 10,
            })
        return AgentResult(
            request=request, selected_workflow_id="WF002",
            steps_executed=[
                self._step(1, "Load product and vendor prices", "price_reader"),
                self._step(2, "Match products by SKU", "csv_reader"),
                self._step(3, "Calculate percentage differences", "calculator"),
                self._step(4, "Flag differences above 10%", "calculator"),
            ],
            result={"validation_report": report, "exception_count": sum(1 for r in report if r.get("exception"))},
        )

    def run_wf003(self, request, context):
        rows = self.tools.call("vendor_file_reader")
        required = ["sku", "product_name"]
        invalid = []
        cleaned = []
        for idx, row in enumerate(rows, start=2):
            normalized = {k.strip().lower().replace(" ", "_"): (v.strip() if isinstance(v, str) else v)
                          for k, v in row.items()}
            missing = self.tools.call("field_validator", row=normalized, required=required)
            if missing:
                invalid.append({"row": idx, "missing_fields": missing, "data": row})
            else:
                cleaned.append(normalized)
        return AgentResult(
            request=request, selected_workflow_id="WF003",
            steps_executed=[
                self._step(1, "Read vendor file", "vendor_file_reader", f"{len(rows)} rows"),
                self._step(2, "Detect and normalize columns", "field_validator"),
                self._step(3, "Validate required fields", "field_validator"),
                self._step(4, "Separate valid and invalid rows", detail=f"{len(invalid)} invalid rows"),
            ],
            result={"cleaned_rows": cleaned, "invalid_rows": invalid, "validation_summary": {
                "input_rows": len(rows), "valid_rows": len(cleaned), "invalid_rows": len(invalid)
            }},
        )

    def run_wf004(self, request, context):
        product = context.get("product") or {
            "product_name": "UrbanTrail Backpack",
            "category": "Travel Backpack",
            "attributes": {"capacity": "28L", "pockets": "7"},
            "material": "recycled polyester",
            "color": "black",
            "target_audience": "urban travelers",
        }
        required = ["product_name", "category"]
        missing = [k for k in required if not product.get(k)]
        optional = ["attributes", "material", "color", "target_audience"]
        missing += [k for k in optional if not product.get(k)]
        product["missing"] = missing
        content = self.llm.generate_product_content(product)
        return AgentResult(
            request=request, selected_workflow_id="WF004",
            steps_executed=[
                self._step(1, "Validate product attributes", "field_validator", f"Missing: {missing or 'none'}"),
                self._step(2, "Generate product description", "llm"),
                self._step(3, "Generate short description", "llm"),
                self._step(4, "Generate SEO title and meta description", "llm"),
            ],
            result=content,
            status="success" if not missing[:2] else "needs_input",
            errors=[] if not missing[:2] else [f"Required fields missing: {', '.join(missing[:2])}"],
        )

    def run_wf005(self, request, context):
        order_id = context.get("order_id")
        if not order_id:
            match = re.search(r"\bORD-\d+\b", request.upper())
            order_id = match.group(0) if match else None
        orders = self.tools.call("order_database")
        if not order_id:
            return AgentResult(
                request=request, selected_workflow_id="WF005", status="needs_input",
                steps_executed=[self._step(1, "Validate order identifier", "field_validator", "Order ID not found in request")],
                result=None, errors=["Please provide an order ID or customer email."]
            )
        order = next((o for o in orders if o["order_id"].upper() == order_id.upper()), None)
        if not order:
            return AgentResult(
                request=request, selected_workflow_id="WF005", status="needs_input",
                steps_executed=[
                    self._step(1, "Validate identifier", "field_validator"),
                    self._step(2, "Search order data", "order_database"),
                ],
                result=None, errors=[f"No order found for {order_id}. Please provide another identifier."]
            )
        shipment = self.tools.call("shipment_lookup", order=order)
        return AgentResult(
            request=request, selected_workflow_id="WF005",
            steps_executed=[
                self._step(1, "Validate identifier", "field_validator"),
                self._step(2, "Search order data", "order_database"),
                self._step(3, "Retrieve order status", "order_database"),
                self._step(4, "Retrieve shipment information", "shipment_lookup"),
                self._step(5, "Summarize current status"),
            ],
            result={"order_id": order["order_id"], "customer_email": order["customer_email"],
                    "status": order["status"], "items": order["items"].split("|"),
                    "shipment": shipment},
        )

    def run_wf006(self, request, context):
        rows = self.tools.call("catalog_reader")
        groups = self.tools.call("duplicate_grouper", rows=rows)

        output = []

        for group in groups:
            if len(group) < 2:
                continue

            anchor = group[0]
            members = []

            # Include the anchor itself in the displayed duplicate group.
            members.append({
                "sku": anchor["sku"],
                "name": anchor["name"],
                "confidence": "anchor",
                "name_similarity": 1.0,
                "attribute_similarity": 1.0,
            })

            # Compare every other product against the anchor.
            for item in group[1:]:
                sku_exact = (
                    item["sku"].strip().lower()
                    == anchor["sku"].strip().lower()
                )

                name_sim = self.tools.call(
                    "text_similarity",
                    a=anchor["name"],
                    b=item["name"],
                )

                attr_sim = self.tools.call(
                    "text_similarity",
                    a=anchor["attributes"],
                    b=item["attributes"],
                )

                confidence = (
                    "definite"
                    if sku_exact
                    else (
                        "high"
                        if name_sim >= 0.86 and attr_sim >= 0.75
                        else "possible"
                    )
                )

                members.append({
                    "sku": item["sku"],
                    "name": item["name"],
                    "confidence": confidence,
                    "name_similarity": round(name_sim, 3),
                    "attribute_similarity": round(attr_sim, 3),
                })

            # Safety check: never return a duplicate group with only one item.
            if len(members) >= 2:
                output.append({
                    "group": members,
                    "group_size": len(members),
                })

        return AgentResult(
            request=request,
            selected_workflow_id="WF006",
            steps_executed=[
                self._step(
                    1,
                    "Load product catalog",
                    "catalog_reader",
                ),
                self._step(
                    2,
                    "Normalize names/SKUs",
                ),
                self._step(
                    3,
                    "Compare identifiers and attributes",
                    "text_similarity",
                ),
                self._step(
                    4,
                    "Group likely duplicates and assign confidence",
                    "duplicate_grouper",
                ),
            ],
            result={
                "duplicate_groups": output,
                "duplicate_group_count": len(output),
            },
        )

    def run_wf007(self, request, context):
        data = context or {}
        missing = [k for k in ["goal", "dates"] if not data.get(k)]
        if missing:
            return AgentResult(
                request=request, selected_workflow_id="WF007", status="needs_input",
                steps_executed=[self._step(1, "Validate campaign inputs", "field_validator")],
                errors=[f"Missing required campaign input(s): {', '.join(missing)}"],
            )
        products = data.get("products", [
            {"name": "UrbanTrail Backpack"}, {"name": "CityPack Sling"}
        ])
        payload = {**data, "products": products}
        brief = self.llm.generate_campaign_content(payload)
        return AgentResult(
            request=request, selected_workflow_id="WF007",
            steps_executed=[
                self._step(1, "Validate inputs", "field_validator"),
                self._step(2, "Identify campaign objective"),
                self._step(3, "Summarize products", "product_data_reader"),
                self._step(4, "Create messaging and channel recommendations", "llm"),
                self._step(5, "Create campaign checklist"),
            ],
            result=brief,
        )

    def run_wf008(self, request, context):
        rows = self.tools.call("keyword_reader")
        output = []
        for r in rows:
            intent = self.tools.call("keyword_classifier", keyword=r["keyword"])
            priority = "high" if intent in {"transactional", "commercial"} else "medium"
            category = r["category"]
            page = f"/{category.lower().replace(' ', '-')}"
            output.append({"keyword": r["keyword"], "intent": intent, "category": category,
                           "priority": priority, "recommended_target_page": page})
        return AgentResult(
            request=request, selected_workflow_id="WF008",
            steps_executed=[
                self._step(1, "Read keywords", "keyword_reader"),
                self._step(2, "Remove duplicates", "keyword_reader"),
                self._step(3, "Classify search intent", "keyword_classifier"),
                self._step(4, "Map keywords to categories/pages"),
                self._step(5, "Identify high-priority keywords and export report"),
            ],
            result={"keyword_report": output},
        )

    def run_wf009(self, request, context):
        data = context or {}
        required = ["task_description", "skills", "priority", "deadline"]
        missing = [k for k in required if not data.get(k)]
        if missing:
            return AgentResult(
                request=request, selected_workflow_id="WF009", status="needs_input",
                steps_executed=[self._step(1, "Understand task requirements", "field_validator")],
                errors=[f"Missing task input(s): {', '.join(missing)}"],
            )
        employees = self.tools.call("employee_database")
        required_skills = {s.lower() for s in data["skills"]}
        ranked = []
        for e in employees:
            matched = required_skills.intersection(e["skills"])
            skill_score = len(matched) / len(required_skills) if required_skills else 0
            capacity_score = min(max(e["capacity_available"], 0) / 10, 1)
            score = 0.7 * skill_score + 0.3 * capacity_score
            if matched and e["capacity_available"] > 0:
                ranked.append((score, e, matched))
        if not ranked:
            return AgentResult(
                request=request, selected_workflow_id="WF009", status="needs_input",
                steps_executed=[
                    self._step(1, "Understand task requirements"),
                    self._step(2, "Compare employee skills", "employee_database"),
                    self._step(3, "Check workload", "employee_database"),
                ],
                errors=["No suitable employee with required skills and available capacity. Escalation required."]
            )
        ranked.sort(key=lambda x: x[0], reverse=True)
        score, employee, matched = ranked[0]
        return AgentResult(
            request=request, selected_workflow_id="WF009",
            steps_executed=[
                self._step(1, "Understand task requirements"),
                self._step(2, "Compare employee skills", "employee_database"),
                self._step(3, "Check current workload", "employee_database"),
                self._step(4, "Rank candidates"),
                self._step(5, "Select employee and generate assignment summary"),
            ],
            result={
                "recommended_employee": employee["name"],
                "reasoning": f"Matched skills: {sorted(matched)}; available capacity: {employee['capacity_available']}",
                "score": round(score, 3),
                "priority": data["priority"],
                "deadline": data["deadline"],
                "task_summary": data["task_description"],
            },
        )

    def run_wf010(self, request, context):
        rows = self.tools.call("execution_log_reader")
        by_wf = defaultdict(list)
        for r in rows:
            by_wf[r["workflow_id"]].append(r)
        report = []
        for wf, entries in by_wf.items():
            total = len(entries)
            failures = sum(1 for e in entries if e["status"] == "failure")
            avg = sum(e["duration_ms"] for e in entries) / total
            slow_steps = Counter(e["step"] for e in entries if e["duration_ms"] > 1000)
            failure_rate = failures / total * 100
            report.append({
                "workflow_id": wf,
                "runs": total,
                "failure_rate_percent": round(failure_rate, 2),
                "average_execution_ms": round(avg, 2),
                "frequent_errors": [e["error"] for e in entries if e["status"] == "failure"][:3],
                "slow_steps": dict(slow_steps),
                "flagged": failure_rate > 10 or avg > 1000,
            })
        report.sort(key=lambda x: x["failure_rate_percent"], reverse=True)
        return AgentResult(
            request=request, selected_workflow_id="WF010",
            steps_executed=[
                self._step(1, "Load execution logs", "execution_log_reader"),
                self._step(2, "Calculate success/failure rates", "calculator"),
                self._step(3, "Calculate average execution time", "calculator"),
                self._step(4, "Identify frequent errors and slow steps"),
                self._step(5, "Generate recommendations"),
            ],
            result={"performance_report": report,
                    "recommendations": [
                        "Investigate workflows flagged for >10% failure rate.",
                        "Profile steps with repeated execution times above 1 second.",
                        "Add targeted retries and input validation around frequent errors.",
                    ]},
        )
