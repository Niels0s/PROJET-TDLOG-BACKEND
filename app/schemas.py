from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import List, Optional

# ==========================
# USERS / AUTH
# ==========================

class UserBase(BaseModel):
    email: EmailStr
    name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserOut(UserBase):
    id: int
    is_superadmin: bool

    class Config:
        orm_mode = True  # warning Pydantic v2 mais ça marche

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

# ==========================
# ÉVÉNEMENTS
# ==========================

class EventBase(BaseModel):
    name: str
    description: Optional[str] = None
    date: datetime
    location: str

class EventCreate(EventBase):
    """Données reçues pour créer un event"""
    pass

class EventOut(EventBase):
    """Données renvoyées au frontend"""
    id: int

    class Config:
        orm_mode = True  # permet de retourner des objets SQLAlchemy


# ==========================
# TICKETS
# ==========================

class TicketCreate(BaseModel):
    user_email: EmailStr
    user_name: str

class TicketsBulkCreate(BaseModel):
    attendees: List[TicketCreate]

class TicketOut(BaseModel):
    id: int
    event_id: int
    user_email: Optional[str] = None
    user_name: str
    qr_code_token: str
    status: str
    scanned_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class ScanRequest(BaseModel):
    token: str


class ScanResult(BaseModel):
    valid: bool          # True si le ticket est accepté
    reason: Optional[str] = None  # ex: "ticket_not_found", "already_scanned"
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    event_id: Optional[int] = None
    status: Optional[str] = None   # UNUSED / SCANNED / CANCELED etc.

# ==========================
# STUDENTS 
# ==========================

class StudentBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    is_external: bool = False

class StudentCreate(StudentBase):
    pass

class Student(StudentBase):
    id: int

    class Config:
        orm_mode = True


# ==========================
# PARTICIPANTS
# ==========================

class ParticipantBase(BaseModel):
    first_name: str
    last_name: str
    promo: Optional[str] = None
    email: Optional[str] = None
    tarif: Optional[str] = None


class ParticipantCreate(ParticipantBase):
    pass


class ParticipantUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    promo: Optional[str] = None
    email: Optional[str] = None
    tarif: Optional[str] = None


class ParticipantOut(ParticipantBase):
    id: int
    event_id: int
    qr_code: str
    status: Optional[str] = None
    scanned_at: Optional[datetime] = None

    class Config:
        orm_mode = True
