import re
import uuid
from datetime import datetime

from pydantic import BaseModel, field_validator, model_validator


# Госномер: только 12 букв, используемых на реальных номерных знаках РФ
_PLATE_RE = re.compile(r"^[АВЕКМНОРСТУХ]\d{3}[АВЕКМНОРСТУХ]{2}\d{2,3}$")


class WeighingRecord(BaseModel):
    id: str | None = None
    dateBefore: str
    dateAfter: str | None = None
    registrationNumber: str
    garbageTruckType: str | None = None
    garbageTruckBrand: str | None = None
    garbageTruckModel: str | None = None
    companyName: str | None = None
    companyInn: str | None = None
    companyKpp: str | None = None
    weightBefore: str
    weightAfter: str
    weightDriver: str | None = None
    coefficient: str | None = None
    garbageWeight: str | None = None
    garbageType: str | None = None
    codeFKKO: str | None = None
    nameFKKO: str | None = None

    @field_validator("registrationNumber")
    @classmethod
    def validate_plate(cls, v: str) -> str:
        v = v.strip().upper()
        if not _PLATE_RE.match(v):
            raise ValueError(f"Неверный формат госномера: {v}")
        return v

    @field_validator("weightBefore", "weightAfter")
    @classmethod
    def validate_weight(cls, v: str) -> str:
        try:
            val = float(v)
        except (ValueError, TypeError):
            raise ValueError(f"Вес должен быть числом: {v}")
        if val <= 0:
            raise ValueError(f"Вес должен быть > 0: {v}")
        return str(int(val))

    @model_validator(mode="after")
    def fill_defaults(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.garbageWeight:
            wb = float(self.weightBefore)
            wa = float(self.weightAfter)
            wd = float(self.weightDriver) if self.weightDriver else 0
            self.garbageWeight = str(int(wb - wa - wd))
        return self
