# app/routers/students.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from .. import models, schemas
from ..db import get_db
import csv
from sqlalchemy.exc import IntegrityError

router = APIRouter(
    prefix="/students",
    tags=["students"],
)

@router.get("/", response_model=list[schemas.Student])
def list_students(db: Session = Depends(get_db)):
    return db.query(models.Student).all()

@router.post("/", response_model=schemas.Student)
def create_student(student: schemas.StudentCreate, db: Session = Depends(get_db)):
    # éviter les doublons d’email
    existing = db.query(models.Student).filter(
        models.Student.email == student.email
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email déjà enregistré")

    db_student = models.Student(**student.dict())
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student


@router.post("/import-csv")
async def import_students_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    content = await file.read()
    text = content.decode("utf-8")
    lines = text.splitlines()

    reader = csv.DictReader(lines, delimiter=";")

    inserted = 0
    skipped_duplicates = 0

    for row in reader:
        first_name = row["first_name"].strip()
        last_name  = row["last_name"].strip()
        email      = row["email"].strip()

        is_external = not (
            email.endswith("@eleves.enpc.fr")
            or email.endswith("@enpc.fr")
        )

        student = models.Student(
            first_name=first_name,
            last_name=last_name,
            email=email,
            is_external=is_external,
        )

        db.add(student)
        try:
            db.commit()          # on essaie d’insérer
            db.refresh(student)
            inserted += 1
        except IntegrityError:
            db.rollback()        # doublon => on annule
            skipped_duplicates += 1
            continue

    return {
        "inserted": inserted,
        "skipped_duplicates": skipped_duplicates,
    }



#autocomplétion
@router.get("/search", response_model=list[schemas.Student])
def search_students(
    q: str = Query("", description="Fragment de nom, prénom ou email"),
    db: Session = Depends(get_db),
):
    if not q:
        # on limite à 20 premiers si q vide
        return (
            db.query(models.Student)
            .order_by(models.Student.last_name)
            .limit(20)
            .all()
        )

    like = f"%{q}%"
    return (
        db.query(models.Student)
        .filter(
            or_(
                models.Student.first_name.ilike(like),
                models.Student.last_name.ilike(like),
                models.Student.email.ilike(like),
            )
        )
        .order_by(models.Student.last_name)
        .limit(20)
        .all()
    )


