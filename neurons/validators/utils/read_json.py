def is_api_data_valid(data):
    if not isinstance(data, dict):
        return False, "Not a dictionary"

    if "keys" not in data.keys():
        return False, "Missing users key"

    if not isinstance(data["keys"], dict):
        return False, "Keys field is not a dict"

    for key, value in data["keys"].items():
        if not isinstance(value, dict):
            return False, "Key value is not a dictionary"
        if "requests_per_min" not in value.keys():
            return False, "Missing requests_per_min field"
        if not isinstance(value["requests_per_min"], int):
            return False, "requests_per_min is not an int"

    return True, "Formatting is good"