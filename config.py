import logging
import os
from functools import lru_cache

from pydantic import AnyUrl, BaseSettings

logger_name = "uvicorn"
log = logging.getLogger(logger_name)


class Settings(BaseSettings):
    environment: str = os.getenv("ENVIRONMENT", "dev")
    debug: bool = os.getenv("DEBUG", False)
    version: str = os.getenv("VERSION", "0.0.1")
    listen_port: int = os.getenv("LISTEN_PORT", 55080)
    doorbell_pin: int = os.getenv("DOORBELL_PIN", 11)  # Physical 11  -> BCM 17
    open_door_pin: int = os.getenv("OPEN_DOOR_PIN", 13)  # Physical 13 -> BCM 27
    open_door_signal_duration: float = os.getenv("OPEN_SIGNAL_DURATION", 0.3)
    open_door_signal_repititions: int = os.getenv("OPEN_SIGNAL_REPETITIONS", 1)
    scheme: str = os.getenv("SCHEME", "https")
    net_location: str = os.getenv("NET_LOCATION", 'astrom.sg')
    route_prefix: str = os.getenv("ROUTE_PREFIX", "/home/door")

    @property
    def base_endpoint(self):
        return f"{self.scheme}://{self.net_location}{self.route_prefix}"

    @property
    def endpoint(self, path=""):
        return f'{self.route_prefix}{path}'

    @property
    def link(self, path=""):
        return f"{self.base_endpoint}{path}"

    @property
    def log(self):
        return log


@lru_cache()
def get_settings() -> Settings:
    log.info("Loading config settings from the environment...")
    return Settings()
