from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text

from app.db import Base


class SystemSettings(Base):
    """
    Single-row table holding MQTT, ThingsBoard push, and download settings.
    Intended to replace most .env configuration (except DB connection itself).
    """

    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)

    # MQTT settings
    mqtt_host = Column(String(255), nullable=False, default="localhost")
    mqtt_port = Column(Integer, nullable=False, default=1883)
    mqtt_username = Column(String(255), nullable=True)
    mqtt_password = Column(String(255), nullable=True)
    mqtt_client_id_prefix = Column(String(255), nullable=False, default="gateway_service")
    mqtt_keepalive = Column(Integer, nullable=False, default=60)
    mqtt_topic_pattern = Column(String(255), nullable=False, default="FM/#")
    mqtt_qos = Column(Integer, nullable=False, default=1)

    # ThingsBoard / telemetry push
    tb_base_url = Column(String(255), nullable=True)
    tb_enable_push = Column(Boolean, nullable=False, default=False)
    tb_enable_auto_push = Column(Boolean, nullable=False, default=False)
    tb_timeout_seconds = Column(String(32), nullable=False, default="5.0")
    tb_device_token = Column(String(255), nullable=True)
    tb_token_from_topic_regex = Column(String(255), nullable=True)
    tb_one_device_per_meter = Column(Boolean, nullable=False, default=False)
    tb_push_interval_seconds = Column(String(32), nullable=False, default="0")
    tb_inactivity_minutes = Column(String(32), nullable=False, default="0")
    tb_inactivity_check_interval_seconds = Column(String(32), nullable=False, default="60")
    tb_inactivity_timeout_seconds = Column(String(32), nullable=False, default="0")

    # ThingsBoard download / credentials
    tb_download_base_url = Column(String(255), nullable=True)
    tb_username = Column(String(255), nullable=True)
    tb_password = Column(String(255), nullable=True)
    tb_device_id = Column(String(64), nullable=True)
    tb_device_ids = Column(Text, nullable=True)  # comma-separated UUIDs
    tb_download_timeout_seconds = Column(String(32), nullable=False, default="30.0")

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class DevicePreset(Base):
    """
    Saved presets for download: label + device UUIDs + keys.
    """

    __tablename__ = "device_presets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    device_ids = Column(Text, nullable=False)  # comma-separated UUIDs
    keys = Column(String(255), nullable=True)  # comma-separated telemetry keys
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

