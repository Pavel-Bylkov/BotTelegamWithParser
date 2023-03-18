import json
from yaml import safe_load, YAMLError, safe_dump


def write_to(file_name: str, data):
    if file_name.endswith(".json"):
        write_json(file_name, data)
    elif file_name.endswith(".yaml") or file_name.endswith(".yml"):
        write_yaml(file_name, data)
    else:
        with open(file_name, "w") as f:
            f.write(data)


def read_from(file_name):
    if file_name.endswith(".json"):
        return read_json(file_name)
    elif file_name.endswith(".yaml") or file_name.endswith(".yml"):
        return read_yaml(file_name)
    else:
        try:
            with open(file_name, "r") as f:
                return f.read()
        except Exception as e:
            print(f"Error load {file_name}", e)
        return ""


def write_json(file_name, data):
    with open(file_name, "w", encoding="utf-8") as file:
        json.dump(data, file, sort_keys=True, ensure_ascii=False)


def read_json(file_name):
    try:
        with open(file_name, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception as e:
        print(f"Error load {file_name}", e)
    return {}


def write_yaml(file_name, data):
    with open(file_name, 'w') as f:
        try:
            safe_dump(data, f)
        except YAMLError as exc:
            print(exc)


def read_yaml(file_name):
    try:
        with open(file_name, 'r') as f:
            try:
                return safe_load(f)
            except YAMLError as exc:
                print(exc)
    except Exception as e:
        print(f"Error load {file_name}", e)
    return {}
