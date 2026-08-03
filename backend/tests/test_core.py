import pytest
from app.config import Settings
from app.domain.entities import MetricValue, TrendDirection
from app.domain.value_objects import ThresholdRule

@pytest.fixture
def mock_settings():
    return Settings(
        app_name="Test Copilot",
        app_env="development",
    )

def test_threshold_rule_evaluation():
    rule = ThresholdRule(
        metric_name="revenue",
        operator="lt",
        value=100.0,
    )
    assert rule.evaluate(50.0) is True
    assert rule.evaluate(150.0) is False

def test_pct_change_threshold():
    rule = ThresholdRule(
        metric_name="revenue",
        operator="pct_change_lt",
        value=15.0,
    )
    # Current 80 vs Previous 100 is -20% change, which is < -15%
    assert rule.evaluate(80.0, 100.0) is True
    # Current 90 vs Previous 100 is -10% change, which is not < -15%
    assert rule.evaluate(90.0, 100.0) is False
