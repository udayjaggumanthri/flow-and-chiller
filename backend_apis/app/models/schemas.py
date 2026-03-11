from datetime import datetime
from typing import Dict, List

from pydantic import BaseModel, Field


class MeterReading(BaseModel):
    meter_id: str = Field(..., description="Identifier of the meter on the gateway")
    flow_rate: float = Field(..., description="Instantaneous flow rate")
    total_consumption: float = Field(..., description="Total accumulated consumption")


class GatewayData(BaseModel):
    gateway_topic: str = Field(..., description="MQTT topic representing the gateway")
    device_id: str = Field(..., description="Gateway device identifier from payload")
    rssi: int = Field(..., description="Signal strength indicator (RSSI)")
    meters: List[MeterReading] = Field(
        default_factory=list, description="List of meter readings for the gateway"
    )
    timestamp: datetime = Field(
        ..., description="Server-side timestamp when data was processed"
    )


class LatestDataResponse(BaseModel):
    gateways: Dict[str, GatewayData] = Field(
        default_factory=dict,
        description="Mapping of gateway topic to its latest data",
    )

