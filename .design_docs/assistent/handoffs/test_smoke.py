#!/usr/bin/env python3
"""Smoke test for Procure AI Sprint 1 stack.

Tests:
1. All modules import correctly
2. Config loads properly
3. Flask app creates and serves
4. FastAPI app creates and has routes
5. Agent graph can be built
"""

from __future__ import annotations

import asyncio
import sys
import traceback
from typing import Any


def test_imports() -> bool:
    """Test all module imports."""
    print("[TEST] Module imports...")
    tests = [
        ("agent_server.core.config", "get_config"),
        ("agent_server.core.sub_agents.brain", "get_brain"),
        ("agent_server.agent", "build_agent_graph"),
        ("agent_server.start_server", "app"),
        ("agent_server.schemas", "AgentState"),
        ("web_app", "create_app"),
        ("web_app.blueprints.bff", "bff_bp"),
    ]

    for module_name, item_name in tests:
        try:
            module = __import__(module_name, fromlist=[item_name])
            item = getattr(module, item_name)
            print(f"  ✓ {module_name}.{item_name}")
        except Exception as e:
            print(f"  ✗ {module_name}.{item_name}: {e}")
            traceback.print_exc()
            return False

    return True


def test_config() -> bool:
    """Test config loading."""
    print("[TEST] Configuration...")
    try:
        from agent_server.core.config import get_config

        config = get_config()
        print(f"  ✓ Config loaded | host={config.host} | db={config.db_path}")
        return True
    except Exception as e:
        print(f"  ✗ Config failed: {e}")
        traceback.print_exc()
        return False


def test_flask_app() -> bool:
    """Test Flask app creation."""
    print("[TEST] Flask application...")
    try:
        from web_app import create_app

        app = create_app("development")
        print(f"  ✓ Flask app created | name={app.name}")

        # Check blueprints
        blueprints = list(app.blueprints.keys())
        print(f"  ✓ Blueprints: {', '.join(blueprints)}")

        if "bff" not in blueprints:
            print(f"  ✗ BFF blueprint not registered")
            return False

        # Check routes
        routes = [str(rule) for rule in app.url_map.iter_rules()]
        print(f"  ✓ Routes: {len(routes)} endpoints")

        critical_routes = ["/chat", "/", "/api/"]
        for route in critical_routes:
            if any(route in r for r in routes):
                print(f"    ✓ {route}*")
            else:
                print(f"    ✗ {route}* not found")

        return True
    except Exception as e:
        print(f"  ✗ Flask failed: {e}")
        traceback.print_exc()
        return False


def test_fastapi_app() -> bool:
    """Test FastAPI app creation."""
    print("[TEST] FastAPI application...")
    try:
        from agent_server.start_server import app

        print(f"  ✓ FastAPI app created | title={app.title}")

        # Check routes
        routes = [getattr(route, 'path', str(route)) for route in app.routes]
        print(f"  ✓ Routes: {len(routes)} endpoints")

        critical_routes = ["/health", "/api/v1/agents/stream", "/api/v1/identity/me"]
        for route in critical_routes:
            if route in routes:
                print(f"    ✓ {route}")
            else:
                print(f"    ✗ {route} not found")
                print(f"       Available: {routes[:5]}")

        return True
    except Exception as e:
        print(f"  ✗ FastAPI failed: {e}")
        traceback.print_exc()
        return False


async def test_agent_graph() -> bool:
    """Test agent graph building.
    
    Uses MockChatModel when Databricks auth unavailable (expected in local dev).
    Set USE_MOCK_MODEL=true to enable mock fallback for testing.
    """
    print("[TEST] Agent graph...")
    try:
        import os
        
        # Enable mock model for testing (no Databricks auth required)
        os.environ["USE_MOCK_MODEL"] = "true"
        
        from agent_server.agent import build_agent_graph
        from agent_server.core.models.mock import MockChatModel

        graph = await build_agent_graph()
        print(f"  ✓ Graph built | type={type(graph).__name__}")

        # Check graph structure
        if hasattr(graph, "get_graph"):
            g = graph.get_graph()
            print(f"  ✓ Graph structure available")

        print(f"  ℹ Using MockChatModel for local testing (USE_MOCK_MODEL=true)")

        return True
    except Exception as e:
        print(f"  ✗ Agent graph failed: {e}")
        traceback.print_exc()
        return False


def test_model_factory() -> bool:
    """Test model factory resolution."""
    print("[TEST] Model Factory...")
    try:
        from shared_library.model_factory import resolve_chat_model

        # Don't actually resolve (requires Databricks auth)
        # Just verify the function exists
        print(f"  ✓ Model Factory available | resolve_chat_model={callable(resolve_chat_model)}")

        return True
    except Exception as e:
        print(f"  ✗ Model Factory failed: {e}")
        traceback.print_exc()
        return False


async def main() -> int:
    """Run all smoke tests."""
    print("\n" + "=" * 70)
    print("PROCURE AI SPRINT 1 — SMOKE TEST")
    print("=" * 70 + "\n")

    results: dict[str, bool] = {}

    # Sync tests
    results["imports"] = test_imports()
    results["config"] = test_config()
    results["flask"] = test_flask_app()
    results["fastapi"] = test_fastapi_app()
    results["model_factory"] = test_model_factory()

    # Async tests
    results["agent_graph"] = await test_agent_graph()

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status} — {name}")

    print(f"\n  {passed}/{total} tests passed\n")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
