from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Hoymiles DTU
    hoymiles_dtu_ip: str

    # Wallbox — use token directly, or email+password for OAuth2
    wallbox_charger_id: str
    wallbox_token: str | None = None
    wallbox_email: str | None = None
    wallbox_password: str | None = None

    # MQTT
    mqtt_host: str = "localhost"
    mqtt_port: int = 1883
    mqtt_username: str = "ems"
    mqtt_password: str = ""

    # EMS
    ems_default_mode: str = "manual"
    ems_threshold_on_w: int = 1400
    ems_threshold_off_w: int = 500
    ems_histeresi_minuts: int = 5
    ems_voltage: int = 230
    ems_phases: int = 3
    ems_poll_interval_s: int = 30

    # InfluxDB
    influxdb_host: str = "localhost"
    influxdb_port: int = 8086
    influxdb_database: str = "ems"
    influxdb_username: str = ""
    influxdb_password: str = ""

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
