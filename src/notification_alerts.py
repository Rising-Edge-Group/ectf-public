from enum import Enum


class FlagAlerts(int, Enum):
    FLAG_DOES_NOT_EXIST = 1
    FLAG_CLAIMED_BEFORE = 2
    FLAG_CLAIMED_FOR_POINTS = 3
    SERVICE_DISCOVERY_REQUIRED = 4
    ACCESS_DENIED = 5
    UNKNOWN = 0
