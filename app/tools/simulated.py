from __future__ import annotations

import csv
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from rapidfuzz.fuzz import ratio


class SimulatedTools:
    """Business tools backed by local sample data. Replace implementations with APIs later."""

    def __init__(self, data_dir: str | Path):
        self.data_dir = Path(data_dir)

    def read_csv(self, filename: str) -> list[dict[str, Any]]:
        with open(self.data_dir / filename, newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def read_inventory(self) -> list[dict[str, Any]]:
        rows = self.read_csv("inventory.csv")
        for r in rows:
            r["current_stock"] = int(r["current_stock"])
            r["minimum_stock"] = int(r["minimum_stock"])
        return rows

    def read_prices(self) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        products = self.read_csv("product_prices.csv")
        vendor = self.read_csv("vendor_prices.csv")
        return products, vendor

    def read_vendor_file(self) -> list[dict[str, Any]]:
        return self.read_csv("vendor_products.csv")

    def read_orders(self) -> list[dict[str, Any]]:
        return self.read_csv("orders.csv")

    def read_catalog(self) -> list[dict[str, Any]]:
        return self.read_csv("catalog.csv")

    def read_keywords(self) -> list[dict[str, Any]]:
        return self.read_csv("keywords.csv")

    def read_employees(self) -> list[dict[str, Any]]:
        rows = self.read_csv("employees.csv")
        for r in rows:
            r["capacity_available"] = int(r["capacity_available"])
            r["skills"] = [x.strip().lower() for x in r["skills"].split("|")]
        return rows

    def read_execution_logs(self) -> list[dict[str, Any]]:
        rows = self.read_csv("execution_logs.csv")
        for r in rows:
            r["duration_ms"] = float(r["duration_ms"])
        return rows

    @staticmethod
    def calculate(a: float, b: float, operation: str) -> float:
        if operation == "subtract":
            return a - b
        if operation == "divide":
            if b == 0:
                raise ZeroDivisionError("Cannot divide by zero")
            return a / b
        if operation == "multiply":
            return a * b
        if operation == "percent_difference":
            return abs(a - b) / b * 100 if b else 0.0
        raise ValueError(f"Unknown operation: {operation}")

    @staticmethod
    def text_similarity(a: str, b: str) -> float:
        return ratio(a.lower(), b.lower()) / 100.0

    @staticmethod
    def validate_fields(row: dict[str, Any], required: list[str]) -> list[str]:
        return [field for field in required if not str(row.get(field, "")).strip()]

    def shipment_lookup(self, order: dict[str, Any]) -> dict[str, Any]:
        return {
            "carrier": order.get("carrier"),
            "tracking_number": order.get("tracking_number"),
            "shipment_status": order.get("shipment_status"),
        }

    def parse_keyword_intent(self, keyword: str) -> str:
        k = keyword.lower()
        if any(x in k for x in ["how to", "what is", "guide", "tips"]):
            return "informational"
        if any(x in k for x in ["buy", "order", "purchase", "near me"]):
            return "transactional"
        if any(x in k for x in ["best", "compare", "price", "review"]):
            return "commercial"
        return "navigational"

    def similarity_group(self, rows: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
        groups: list[list[dict[str, Any]]] = []
        used: set[int] = set()
        for i, a in enumerate(rows):
            if i in used:
                continue
            group = [a]
            used.add(i)
            for j in range(i + 1, len(rows)):
                if j in used:
                    continue
                b = rows[j]
                sku_exact = a["sku"].strip().lower() == b["sku"].strip().lower()
                name_sim = self.text_similarity(a["name"], b["name"])
                attr_sim = self.text_similarity(a["attributes"], b["attributes"])
                if sku_exact or (name_sim >= 0.86 and attr_sim >= 0.75):
                    group.append(b)
                    used.add(j)
            if len(group) > 1:
                groups.append(group)
        return groups
