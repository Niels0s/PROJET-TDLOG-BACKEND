from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import secrets
from typing import Dict, Optional

from app.db import get_db
from app import models, schemas
from app.deps import get_current_user

router = APIRouter(prefix="/events/{event_id}/participants", tags=["participants"])


def _get_event_or_404(event_id: int, db: Session) -> models.Event:
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event non trouvé")
    return event


def _get_participant_or_404(event_id: int, participant_id: int, db: Session) -> models.Participant:
    participant = (
        db.query(models.Participant)
        .filter(
            models.Participant.id == participant_id,
            models.Participant.event_id == event_id,
        )
        .first()
    )
    if not participant:
        raise HTTPException(status_code=404, detail="Participant non trouvé")
    return participant


def _generate_qr_code() -> str:
    return secrets.token_urlsafe(16)


def _participant_to_out(
    participant: models.Participant,
    ticket: Optional[models.Ticket],
) -> schemas.ParticipantOut:
    return schemas.ParticipantOut(
        id=participant.id,
        event_id=participant.event_id,
        first_name=participant.first_name,
        last_name=participant.last_name,
        promo=participant.promo,
        email=participant.email,
        tarif=participant.tarif,
        qr_code=participant.qr_code,
        status=ticket.status if ticket else None,
        scanned_at=ticket.scanned_at if ticket else None,
    )


@router.get("/", response_model=list[schemas.ParticipantOut])
def list_participants(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _get_event_or_404(event_id, db)
    participants = (
        db.query(models.Participant)
        .filter(models.Participant.event_id == event_id)
        .order_by(models.Participant.last_name)
        .all()
    )
    qr_codes = [p.qr_code for p in participants]
    tickets_by_qr: Dict[str, models.Ticket] = {}
    if qr_codes:
        tickets = (
            db.query(models.Ticket)
            .filter(models.Ticket.qr_code_token.in_(qr_codes))
            .all()
        )
        tickets_by_qr = {t.qr_code_token: t for t in tickets}

    return [
        _participant_to_out(p, tickets_by_qr.get(p.qr_code))
        for p in participants
    ]


@router.post("/", response_model=schemas.ParticipantOut, status_code=status.HTTP_201_CREATED)
def create_participant(
    event_id: int,
    participant_in: schemas.ParticipantCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _get_event_or_404(event_id, db)

    participant = models.Participant(
        event_id=event_id,
        first_name=participant_in.first_name,
        last_name=participant_in.last_name,
        promo=participant_in.promo,
        email=participant_in.email,
        tarif=participant_in.tarif,
        qr_code=_generate_qr_code(),
    )
    db.add(participant)
    db.commit()
    db.refresh(participant)

    ticket = models.Ticket(
        event_id=event_id,
        user_email=participant.email,  # None si non fourni
        user_name=f"{participant.first_name} {participant.last_name}".strip(),
        qr_code_token=participant.qr_code,
        status="UNUSED",
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    return _participant_to_out(participant, ticket)


@router.put("/{participant_id}", response_model=schemas.ParticipantOut)
def update_participant(
    event_id: int,
    participant_id: int,
    participant_in: schemas.ParticipantUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _get_event_or_404(event_id, db)
    participant = _get_participant_or_404(event_id, participant_id, db)

    for field, value in participant_in.dict(exclude_unset=True).items():
        setattr(participant, field, value)

    db.commit()
    db.refresh(participant)

    ticket = (
        db.query(models.Ticket)
        .filter(models.Ticket.qr_code_token == participant.qr_code)
        .first()
    )
    if ticket:
        ticket.user_email = participant.email  # None si non fourni
        ticket.user_name = f"{participant.first_name} {participant.last_name}".strip()
        db.commit()

    return _participant_to_out(participant, ticket)


@router.delete("/{participant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_participant(
    event_id: int,
    participant_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _get_event_or_404(event_id, db)
    participant = _get_participant_or_404(event_id, participant_id, db)
    ticket = (
        db.query(models.Ticket)
        .filter(models.Ticket.qr_code_token == participant.qr_code)
        .first()
    )
    db.delete(participant)
    if ticket:
        db.delete(ticket)
    db.commit()
