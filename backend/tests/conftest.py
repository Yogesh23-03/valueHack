"""Shared pytest fixtures for the engine test suite."""

from __future__ import annotations

import pathlib
import sys

import pytest

BACKEND_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

GOLDEN_DIR = pathlib.Path(__file__).resolve().parent / "golden"


@pytest.fixture(scope="session")
def business():
    from app.engine.adapters import business_from_dict
    from app.seed import demo_business_dict

    return business_from_dict(demo_business_dict())


@pytest.fixture()
def client():
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as c:
        yield c
