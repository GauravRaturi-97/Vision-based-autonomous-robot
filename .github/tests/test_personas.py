"""
Unit tests for AURA-Fleet Persona Knowledge Bases and Dispatch Logic
"""
import sys
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PERSONAS_DIR = os.path.join(HERE, "..", "controllers", "vision_bot_olama", "personas")
sys.path.insert(0, PERSONAS_DIR)

import cafe_barista  # noqa: E402
import factory_safety  # noqa: E402
import warehouse_logistics  # noqa: E402
import hospital_nurse  # noqa: E402


def test_cafe_barista():
    res = cafe_barista.analyze_cafe_request("I want a hot cappuccino", "cappuccino")
    assert res is not None
    assert "tf_query" in res
    assert "card_title" in res
    assert len(res["custom_lines"]) > 0


def test_factory_safety():
    res = factory_safety.analyze_factory_request("inspect the conveyor belt emergency stop", "conveyor")
    assert res is not None
    assert "tf_query" in res
    assert "OSHA" in res["card_title"]
    assert len(res["custom_lines"]) > 0


def test_warehouse_logistics():
    res = warehouse_logistics.analyze_warehouse_request("transport the wooden box to dock", "box")
    assert res is not None
    assert "tf_query" in res
    assert "card_title" in res
    assert len(res["custom_lines"]) > 0


def test_hospital_nurse():
    res = hospital_nurse.analyze_hospital_request("deliver IV saline to bed 1", "bed 1")
    assert res is not None
    assert "tf_query" in res
    assert "card_title" in res
    assert len(res["custom_lines"]) > 0
