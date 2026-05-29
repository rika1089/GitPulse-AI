"""
tools/
------
MCP tool registration layer.

Each module registers one logical group of tools.
All business logic lives in services/ — tools are thin dispatch wrappers
that validate inputs and delegate, keeping main.py clean.
"""
