"""Compare direct model fields with wrapped and standalone fields validators."""

import json

import pytest

from pydantic_core import SchemaValidator, core_schema


@pytest.mark.parametrize('input_mode', ['python', 'json', 'json-in-json'])
@pytest.mark.parametrize('schema_kind', ['direct', 'before', 'wrap', 'fields'])
@pytest.mark.parametrize('model_count', [1, 100])
def test_model_fields_result(benchmark, input_mode, schema_kind, model_count):
    class Model:
        __slots__ = '__dict__', '__pydantic_fields_set__', '__pydantic_extra__', '__pydantic_private__'

    fields = core_schema.model_fields_schema(
        {
            'name': core_schema.model_field(core_schema.str_schema()),
            'value': core_schema.model_field(core_schema.int_schema()),
        }
    )
    if schema_kind == 'before':
        fields = core_schema.no_info_before_validator_function(lambda value: value, fields)
    elif schema_kind == 'wrap':
        fields = core_schema.no_info_wrap_validator_function(lambda value, handler: handler(value), fields)
    schema = fields if schema_kind == 'fields' else core_schema.model_schema(Model, fields)
    schema = core_schema.list_schema(schema)
    if input_mode == 'json-in-json':
        schema = core_schema.json_schema(schema)
    validator = SchemaValidator(schema)
    data = [{'name': 'example', 'value': 1}] * model_count
    if input_mode != 'python':
        if input_mode == 'json-in-json':
            data = json.dumps(data)
        data = json.dumps(data).encode()
        validate = validator.validate_json
    else:
        validate = validator.validate_python
    result = validate(data)
    assert len(result) == model_count
    if schema_kind == 'fields':
        assert result[0] == ({'name': 'example', 'value': 1}, None, {'name', 'value'})
    else:
        assert result[0].__dict__ == {'name': 'example', 'value': 1}
        assert result[0].__pydantic_extra__ is None
        assert result[0].__pydantic_fields_set__ == {'name', 'value'}
    benchmark(validate, data)
