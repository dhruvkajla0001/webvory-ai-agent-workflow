from __future__ import annotations

from typing import Any

from .registry import ToolRegistry
from .simulated import SimulatedTools


def build_tool_registry(data_dir: str) -> ToolRegistry:
    data = SimulatedTools(data_dir)
    registry = ToolRegistry()

    registry.register("csv_reader", "Read CSV business data", data.read_csv)
    registry.register("inventory_reader", "Read inventory records", data.read_inventory)
    registry.register("price_reader", "Read internal and vendor prices", data.read_prices)
    registry.register("vendor_file_reader", "Read vendor product file", data.read_vendor_file)
    registry.register("order_database", "Read simulated order database", data.read_orders)
    registry.register("shipment_lookup", "Lookup shipment details", data.shipment_lookup)
    registry.register("catalog_reader", "Read product catalog", data.read_catalog)
    registry.register("keyword_reader", "Read keyword list", data.read_keywords)
    registry.register("employee_database", "Read employee/task capacity data", data.read_employees)
    registry.register("execution_log_reader", "Read workflow execution logs", data.read_execution_logs)
    registry.register("calculator", "Perform deterministic arithmetic", data.calculate)
    registry.register("text_similarity", "Calculate normalized text similarity", data.text_similarity)
    registry.register("field_validator", "Validate required fields", data.validate_fields)
    registry.register("keyword_classifier", "Classify search intent", data.parse_keyword_intent)
    registry.register("duplicate_grouper", "Group likely duplicate products", data.similarity_group)
    return registry
