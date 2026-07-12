"""Strategy engine unit test skeletons."""

import pytest


@pytest.mark.skip(reason="skeleton")
def test_strategy_builder_add_legs() -> None:
    """Builder should support unlimited legs."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_leg_converter_to_payoff() -> None:
    """Leg converter should map strategy legs to payoff legs."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_strategy_recognition_long_call() -> None:
    """Recognizer should identify long call for display."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_strategy_recognition_iron_condor() -> None:
    """Recognizer should identify iron condor pattern."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_engine_orchestration_order() -> None:
    """Orchestrator should call engines in dependency order."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_evaluation_service_no_local_math() -> None:
    """Evaluation should delegate all calculations to frozen engines."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_strategy_scoring_from_engine_outputs() -> None:
    """Scoring should map engine results without formulas."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_strategy_comparison_ranking() -> None:
    """Comparison service should rank by overall score."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_template_from_builtin() -> None:
    """Template service should instantiate strategy from template."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_strategy_serialization_json() -> None:
    """Serializer should export and import strategy JSON."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_strategy_service_lifecycle() -> None:
    """Service should create, evaluate, and delete strategies."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_batch_evaluation_performance() -> None:
    """Batch evaluation should target 100 strategies/sec."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_optimization_framework_placeholder() -> None:
    """Optimization framework should return not-implemented status."""
    pass
