from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.db_models import DevicePreset


router = APIRouter(prefix="/device-presets", tags=["device-presets"])


class DevicePresetIn(BaseModel):
    name: str
    device_ids: List[str]
    keys: str


class DevicePresetOut(BaseModel):
    id: int
    name: str
    device_ids: List[str]
    keys: str

    class Config:
        from_attributes = True


@router.get("", response_model=List[DevicePresetOut])
def list_device_presets(db: Session = Depends(get_db)) -> List[DevicePresetOut]:
    presets = db.query(DevicePreset).order_by(DevicePreset.name.asc()).all()
    out: List[DevicePresetOut] = []
    for p in presets:
        ids = [x.strip() for x in (p.device_ids or "").split(",") if x.strip()]
        out.append(DevicePresetOut(id=p.id, name=p.name, device_ids=ids, keys=p.keys or ""))
    return out


@router.post("", response_model=DevicePresetOut)
def create_device_preset(payload: DevicePresetIn, db: Session = Depends(get_db)) -> DevicePresetOut:
    trimmed_name = payload.name.strip()
    if not trimmed_name:
        raise HTTPException(status_code=400, detail="Preset name is required.")
    # Optional uniqueness enforcement
    existing = (
        db.query(DevicePreset)
        .filter(DevicePreset.name == trimmed_name)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="A preset with this name already exists.")

    row = DevicePreset(
        name=trimmed_name,
        device_ids=",".join(payload.device_ids),
        keys=payload.keys.strip(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    ids = [x.strip() for x in (row.device_ids or "").split(",") if x.strip()]
    return DevicePresetOut(id=row.id, name=row.name, device_ids=ids, keys=row.keys or "")


@router.delete("/{preset_id}", status_code=204)
def delete_device_preset(preset_id: int, db: Session = Depends(get_db)) -> None:
    row = db.query(DevicePreset).filter(DevicePreset.id == preset_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Preset not found.")
    db.delete(row)
    db.commit()

