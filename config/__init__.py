from envyaml import EnvYAML
from config.constants import CONFIG_YAML_NAME

config = EnvYAML(f"config/{CONFIG_YAML_NAME}")

KAFKA_CONFIG = config["kafka"]
GIT_CONFIG = config["git"]
GENERAL_CONFIG = config["general"]
CERTS_CONFIG = config["certs"]
LOGS_CONFIG = config["logs"]
