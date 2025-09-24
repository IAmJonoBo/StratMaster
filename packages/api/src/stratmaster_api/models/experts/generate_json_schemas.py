"""JSON schema generator for Expert Council models."""

import json

from pydantic.json_schema import models_json_schema

from .schema_registry import REGISTRY


def main():
    """Generate and print JSON schemas for Expert Council models."""
    core_schema, defs = models_json_schema(models=REGISTRY, title="StratMaster Experts", components=None)
    print(json.dumps(core_schema, indent=2))
    if defs:
        print("\nDefinitions:")
        print(json.dumps(defs, indent=2))


if __name__ == "__main__":
    main()