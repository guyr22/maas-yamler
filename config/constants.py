PROD_ENV = "production"
CONFIG_YAML_NAME = "config.yaml"
BLACKBOX_CONFIGURATION = [
    {
        "source_labels": ["__address__"],
        "seperator": ";",
        "regex": "(.*)",
        "target_label": "__param_target",
        "replacement": "$1",
        "action": "replace",
    },
    {
        "source_labels": ["__param_target"],
        "seperator": ":",
        "regex": "(.*)",
        "target_label": "instance",
        "replacement": "$1",
        "action": "replace",
    },
    {
        "seperator": ";",
        "regex": "(.*)",
        "target_label": "__address__",
        "action": "replace",
    },
]
