"""Round-trip tests for the generic dataclass<->JSON codec, covering every
type it needs to handle first with synthetic dataclasses (isolating each
type independently), then with the real domain models it will actually be
used to persist (Strategy, Portfolio, BacktestResult).
"""

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from enum import Enum

from app.persistence.dataclass_codec import from_json, to_json


class _Color(str, Enum):
    RED = "red"
    BLUE = "blue"


@dataclass(frozen=True, slots=True)
class _Leaf:
    name: str
    count: int
    ratio: float
    active: bool
    amount: Decimal
    color: _Color
    when: datetime
    day: date
    duration: timedelta
    note: str | None = None


@dataclass(frozen=True, slots=True)
class _Branch:
    label: str
    leaves: tuple[_Leaf, ...]
    optional_leaf: _Leaf | None = None


def _leaf(note: str | None = None) -> _Leaf:
    return _Leaf(
        name="leaf-1", count=3, ratio=0.5, active=True, amount=Decimal("12.50"),
        color=_Color.BLUE, when=datetime(2026, 8, 16, 10, 30, tzinfo=timezone.utc),
        day=date(2026, 8, 16), duration=timedelta(days=1, hours=2), note=note,
    )


class TestPrimitiveTypesRoundTrip:
    def test_str_int_float_bool(self) -> None:
        leaf = _leaf()

        restored = from_json(_Leaf, to_json(leaf))

        assert restored.name == leaf.name
        assert restored.count == leaf.count
        assert restored.ratio == leaf.ratio
        assert restored.active is True

    def test_decimal_round_trips_exactly_no_float_drift(self) -> None:
        leaf = _leaf()

        restored = from_json(_Leaf, to_json(leaf))

        assert restored.amount == Decimal("12.50")
        assert isinstance(restored.amount, Decimal)

    def test_datetime_round_trips_with_timezone(self) -> None:
        leaf = _leaf()

        restored = from_json(_Leaf, to_json(leaf))

        assert restored.when == leaf.when
        assert restored.when.tzinfo is not None

    def test_date_round_trips(self) -> None:
        leaf = _leaf()

        restored = from_json(_Leaf, to_json(leaf))

        assert restored.day == date(2026, 8, 16)

    def test_timedelta_round_trips(self) -> None:
        leaf = _leaf()

        restored = from_json(_Leaf, to_json(leaf))

        assert restored.duration == timedelta(days=1, hours=2)

    def test_enum_round_trips_to_correct_member(self) -> None:
        leaf = _leaf()

        restored = from_json(_Leaf, to_json(leaf))

        assert restored.color is _Color.BLUE


class TestOptionalFields:
    def test_none_value_round_trips_as_none(self) -> None:
        leaf = _leaf(note=None)

        restored = from_json(_Leaf, to_json(leaf))

        assert restored.note is None

    def test_present_optional_value_round_trips(self) -> None:
        leaf = _leaf(note="a note")

        restored = from_json(_Leaf, to_json(leaf))

        assert restored.note == "a note"

    def test_optional_nested_dataclass_none(self) -> None:
        branch = _Branch(label="b", leaves=(), optional_leaf=None)

        restored = from_json(_Branch, to_json(branch))

        assert restored.optional_leaf is None

    def test_optional_nested_dataclass_present(self) -> None:
        branch = _Branch(label="b", leaves=(), optional_leaf=_leaf())

        restored = from_json(_Branch, to_json(branch))

        assert restored.optional_leaf == _leaf()


class TestNestedDataclassesAndTuples:
    def test_tuple_of_nested_dataclasses_round_trips_in_order(self) -> None:
        branch = _Branch(label="root", leaves=(_leaf("a"), _leaf("b"), _leaf("c")))

        restored = from_json(_Branch, to_json(branch))

        assert [leaf.note for leaf in restored.leaves] == ["a", "b", "c"]
        assert restored.leaves == branch.leaves

    def test_empty_tuple_round_trips_as_empty_tuple_not_none(self) -> None:
        branch = _Branch(label="root", leaves=())

        restored = from_json(_Branch, to_json(branch))

        assert restored.leaves == ()
        assert isinstance(restored.leaves, tuple)

    def test_full_object_equality_after_round_trip(self) -> None:
        branch = _Branch(label="root", leaves=(_leaf("x"),), optional_leaf=_leaf("y"))

        restored = from_json(_Branch, to_json(branch))

        assert restored == branch
