def validate_against_schema(attributes: dict, schema: dict) -> dict:
    errors = {}
    type_map = {'string': str, 'integer': int, 'number': (int, float), 'boolean': bool}

    for field_name, rules in schema.items():
        required = rules.get('required', False)
        value = attributes.get(field_name)

        if required and value is None:
            errors[field_name] = "This field is required."
            continue

        if value is not None:
            expected_type = rules.get('type')
            py_type = type_map.get(expected_type)
            if py_type and not isinstance(value, py_type):
                errors[field_name] = f"Should be of type {expected_type}."

    return errors