from pydantic import BaseModel


class AvailabilitySlot(BaseModel):
    date: str
    hour: int
    available: int
    total: int
    unavailable_employee_ids: list[int]


class AvailabilityResponse(BaseModel):
    month: int
    year: int
    total: int
    slots: list[AvailabilitySlot]
