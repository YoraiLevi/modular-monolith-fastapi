# config_loader.py
import yaml
import jsonschema
from jsonschema import validate
from pathlib import Path

config_path = Path().parent / "config.yaml"  # TODO: make this configurable from the command line


def load_config(file_path: str | Path, schema_path: str | Path | None = None) -> dict:
    """
    Load and validate the YAML configuration file against a schema.

    :param file_path: Path to the YAML configuration file.
    :param schema_path: Path to the YAML schema file, if None, no schema validation is performed
    :return: Validated configuration as a dictionary.
    :raises FileNotFoundError: If the file does not exist.
    :raises yaml.YAMLError: If there is an error parsing the YAML file.
    :raises jsonschema.exceptions.ValidationError: If the configuration does not match the schema.
    """
    config_path = Path(file_path)
    schema_path = Path(schema_path) if schema_path is not None else None

    try:
        with config_path.open("r") as file:
            config = yaml.safe_load(file)
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found: {config_path.resolve()}")
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Error parsing YAML file: {e}")

    if schema_path is not None:
        try:
            with schema_path.open("r") as schema_file:
                schema = yaml.safe_load(schema_file)
            validate(instance=config, schema=schema)
        except jsonschema.exceptions.ValidationError as e:  # type: ignore
            raise ValueError(f"Configuration validation error: {e.message}")

    return config
