"""SQLAlchemy models and DB helper."""
from datetime import datetime

import enum

from sqlalchemy import (
    create_engine,
    Integer,
    String,
    Float,
    Date,
    DateTime,
    Boolean,
    ForeignKey,
    func,
    Enum,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

engine = create_engine("sqlite:///lawyers.db", echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, future=True)
Base = declarative_base()


class Lawyer(Base):
    __tablename__ = "lawyers"
    id = Integer(primary_key=True, autoincrement=True)
    full_name = String(255, unique=True, nullable=False)
    years_experience = Float(default=0)
    start_rating = Float(default=1000)
    current_rating = Float(default=1000)
    last_active = Date()
    active = Boolean(default=True)

    cases = relationship("Case", back_populates="lawyer", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="lawyer", cascade="all, delete-orphan")
    penalties = relationship("Penalty", back_populates="lawyer", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Lawyer {self.full_name}: {self.current_rating:.1f}>"


class CaseOutcome(enum.Enum):
    FULL_WIN = "полная победа"
    PARTIAL_WIN = "частичная победа"
    SETTLEMENT = "мировое"
    LOSS = "поражение"


class Case(Base):
    __tablename__ = "cases"
    id = Integer(primary_key=True, autoincrement=True)
    lawyer_id = Integer(ForeignKey("lawyers.id"))
    date = Date()
    complexity = Integer()  # 1–5 scale
    outcome = Enum(CaseOutcome, name="case_outcome_enum")

    lawyer = relationship("Lawyer", back_populates="cases")


class Review(Base):
    __tablename__ = "reviews"
    id = Integer(primary_key=True, autoincrement=True)
    lawyer_id = Integer(ForeignKey("lawyers.id"))
    date = Date()
    score = Float()  # 1–5

    lawyer = relationship("Lawyer", back_populates="reviews")


class Penalty(Base):
    __tablename__ = "penalties"
    id = Integer(primary_key=True, autoincrement=True)
    lawyer_id = Integer(ForeignKey("lawyers.id"))
    date = Date()
    reason = String(255)

    lawyer = relationship("Lawyer", back_populates="penalties")


class RatingHistory(Base):
    __tablename__ = "rating_history"
    id = Integer(primary_key=True, autoincrement=True)
    lawyer_id = Integer(ForeignKey("lawyers.id"))
    timestamp = DateTime(default=datetime.utcnow)
    rating = Float()

    lawyer = relationship("Lawyer")


def init_db():
    Base.metadata.create_all(engine)


def get_session():
    return SessionLocal()


if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print("Database initialized.")

