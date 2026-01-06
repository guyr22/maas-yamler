from enum import Enum


class JobType(Enum):
    GENERAL = "general"
    BLACKBOX = "blackbox"
    HTTP_SD = "http_sd"
    KUBERNETES_SD = "kubernetes_sd"
    