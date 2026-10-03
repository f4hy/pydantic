"""Exercise JSON model extras allocation, including the extra=allow control cases."""

import json

import pytest

from pydantic_core import SchemaValidator, core_schema


@pytest.mark.parametrize(
    'extra_behavior,extra_count', [('ignore', 0), ('ignore', 100), ('forbid', 0), ('allow', 0), ('allow', 100)]
)
@pytest.mark.parametrize('model_count', [1, 100])
def test_json_model_extras(benchmark, extra_behavior, extra_count, model_count):
    class Model:
        __slots__ = '__dict__', '__pydantic_fields_set__', '__pydantic_extra__', '__pydantic_private__'

    validator = SchemaValidator(
        core_schema.list_schema(
            core_schema.model_schema(
                Model,
                core_schema.model_fields_schema(
                    {'value': core_schema.model_field(core_schema.int_schema())},
                    extra_behavior=extra_behavior,
                ),
            )
        )
    )
    item = {'value': 1, **{f'extra_{i}': i for i in range(extra_count)}}
    data = json.dumps([item] * model_count).encode()
    result = validator.validate_json(data)
    assert len(result) == model_count
    assert result[0].__dict__ == {'value': 1}
    expected_extra = {f'extra_{i}': i for i in range(extra_count)} if extra_behavior == 'allow' else None
    assert result[0].__pydantic_extra__ == expected_extra
    benchmark(validator.validate_json, data)
