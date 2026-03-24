import pytest
from unittest.mock import MagicMock, patch
from backend.rules.models import AlertRecord, Severity
from backend.rules.definitions import LabRow
from backend.rules.engine import _apply_environmental_modifiers

def test_environmental_modifiers_breathing():
    # AQI > 100 should bump severity for abnormal_wbc
    alerts = [
        AlertRecord(rule_id="abnormal_wbc", triggered=True, severity=Severity.MEDIUM, reason="High WBC")
    ]
    env_data = {"aqi": 120, "temperature": 25, "humidity": 50}
    _apply_environmental_modifiers(alerts, env_data)
    
    # Assert string mapping since aqi > 100
    assert alerts[0].severity == Severity.HIGH
    assert "poor air quality" in alerts[0].reason
    assert alerts[0].environmental_evidence is not None
    assert alerts[0].environmental_evidence["aqi"] == 120

def test_environmental_modifiers_sleep():
    # Temp > 30 should bump severity for low_vitamin_d
    alerts = [
        AlertRecord(rule_id="low_vitamin_d", triggered=True, severity=Severity.LOW, reason="Low Vit D")
    ]
    env_data = {"aqi": 50, "temperature": 32, "humidity": 60}
    _apply_environmental_modifiers(alerts, env_data)
    
    assert alerts[0].severity == Severity.MEDIUM
    assert "high temperature" in alerts[0].reason
    assert alerts[0].environmental_evidence is not None
    assert alerts[0].environmental_evidence["temperature"] == 32

def test_environmental_modifiers_extreme():
    # Extreme weather should adjust reason but not bump severity directly for activity rules
    alerts = [
        AlertRecord(rule_id="any_abnormal", triggered=True, severity=Severity.MEDIUM, reason="Some random abnormal")
    ]
    env_data = {"aqi": 160, "temperature": 30, "humidity": 50}
    _apply_environmental_modifiers(alerts, env_data)
    
    assert alerts[0].severity == Severity.MEDIUM  # unchanged
    assert "Take extra precaution with activity due to extreme weather" in alerts[0].reason
    assert alerts[0].environmental_evidence["aqi"] == 160

def test_environmental_modifiers_null_safe():
    # Missing optional env data shouldn't crash
    alerts = [
        AlertRecord(rule_id="any_abnormal", triggered=True, severity=Severity.MEDIUM, reason="Some random abnormal")
    ]
    env_data = {"aqi": None, "temperature": None, "humidity": None}
    _apply_environmental_modifiers(alerts, env_data)
    
    assert alerts[0].severity == Severity.MEDIUM
    assert alerts[0].environmental_evidence is None
