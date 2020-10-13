import logging
import os
from functools import lru_cache
from datetime import datetime

from pydantic import AnyUrl, BaseSettings




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
    logdir: str = os.getenv("PINTU_LOG_DIR", "/home/pi/pintu/logs")
    net_location: str = os.getenv("NET_LOCATION", 'astrom.sg')
    route_prefix: str = os.getenv("ROUTE_PREFIX", "/home/door")
    doorbell_url: str = os.getenv(
        "DOORBELL_URL",
        "http://vanaheim.astro:8000/cast/assistants/say/?text=dingdong%2C%20dingdong%21%20There%20is%20someone%20at%20the%20door"
    )

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
    # log.info("Loading config settings from the environment...")
    return Settings()


current_time = datetime.utcnow()
date_str = current_time.strftime('%y%m%d')
config = get_settings()
log_file = os.path.join(config.logdir, f"{date_str}_pintu.log")
logging.basicConfig(
    filename=log_file,
    filemode='a',
    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
    datefmt='%H:%M:%S',
    level=logging.DEBUG
)
logger_name = "uvicorn"
log = logging.getLogger(logger_name)