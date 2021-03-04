from agero_python_configuration import BaseConfig


class LoggerConfig(BaseConfig):
    environment: str
    application_name: str
    global_log_level: str
