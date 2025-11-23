from pydantic import BaseModel
from datetime import datetime

class EventCreate(BaseModel):
    name: str
    description: str | None = None
    date: datetime
    location: str

class TicketCreate(BaseModel):
    user_email: str
    user_name: str

class ScanRequest(BaseModel):
    token: str
