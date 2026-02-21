from typing import Any, Dict

import pytest

from plf.utils import Component


class LegacyListArgsComponent(Component):
    def __init__(self):
        super().__init__()
        self.args = ["alpha", "beta"]
        self.payload = None

    def _setup(self, args: Dict[str, Any], P=None):
        self.payload = args


class LegacyDictArgsComponent(Component):
    def __init__(self):
        super().__init__()
        self.args = {"alpha": "legacy_default", "beta": 0}
        self.payload = None

    def _setup(self, args: Dict[str, Any], P=None):
        self.payload = args


class TypedArgsComponent(Component):
    def __init__(self):
        super().__init__()
        self.args = {
            "epochs": int,
            "name": (str, bytes),
            "ratio": lambda x: 0 <= x <= 1,
        }
        self.payload = None

    def _setup(self, args: Dict[str, Any], P=None):
        self.payload = args


class CustomCheckArgsComponent(Component):
    def __init__(self):
        super().__init__()
        self.args = ["value"]

    def check_args(self, args: dict) -> bool:
        return args.get("value", 0) > 0

    def _setup(self, args: Dict[str, Any], P=None):
        return None


def test_backward_compatible_list_required_keys():
    component = LegacyListArgsComponent()

    assert component.setup({"alpha": 1, "beta": 2, "extra": True}) is component
    assert component.payload["extra"] is True


def test_backward_compatible_dict_required_keys_without_forcing_literal_values():
    component = LegacyDictArgsComponent()

    assert component.setup({"alpha": 10, "beta": "not_the_default"}) is component


def test_missing_required_keys_raise_clean_value_error():
    component = LegacyListArgsComponent()

    with pytest.raises(ValueError, match=r"Missing required argument\(s\)"):
        component.setup({"alpha": 1})


def test_non_dict_args_raise_clean_type_error():
    component = LegacyListArgsComponent()

    with pytest.raises(TypeError, match="must be a dict"):
        component.setup(["alpha", "beta"])  # type: ignore[arg-type]


def test_optional_typed_validation_works_for_type_and_callable():
    component = TypedArgsComponent()

    assert component.setup({"epochs": 3, "name": "run", "ratio": 0.5}) is component

    with pytest.raises(TypeError, match="Invalid type for 'epochs'"):
        component.setup({"epochs": "3", "name": "run", "ratio": 0.5})

    with pytest.raises(ValueError, match="Validation failed for 'ratio'"):
        component.setup({"epochs": 3, "name": "run", "ratio": 1.5})


def test_custom_check_args_still_supported():
    component = CustomCheckArgsComponent()

    assert component.setup({"value": 1}) is component

    with pytest.raises(ValueError, match="incompatible"):
        component.setup({"value": 0})
