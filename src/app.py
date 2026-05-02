"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
from pathlib import Path
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker, relationship, Mapped, mapped_column
from fastapi import Depends

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# Database setup
DATABASE_URL = "sqlite:///./activities.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Models
class Club(Base):
    __tablename__ = "clubs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True, index=True)
    events: Mapped[list["Event"]] = relationship("Event", back_populates="club")

class Event(Base):
    __tablename__ = "events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True, index=True)
    description: Mapped[str] = mapped_column(Text)
    schedule: Mapped[str] = mapped_column(String)
    max_participants: Mapped[int] = mapped_column(Integer)
    club_id: Mapped[int] = mapped_column(Integer, ForeignKey("clubs.id"))
    club: Mapped["Club"] = relationship("Club", back_populates="events")
    attendances: Mapped[list["Attendance"]] = relationship("Attendance", back_populates="event")

class Student(Base):
    __tablename__ = "students"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    attendances: Mapped[list["Attendance"]] = relationship("Attendance", back_populates="student")

class Attendance(Base):
    __tablename__ = "attendances"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    event_id: Mapped[int] = mapped_column(Integer, ForeignKey("events.id"))
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id"))
    event: Mapped["Event"] = relationship("Event", back_populates="attendances")
    student: Mapped["Student"] = relationship("Student", back_populates="attendances")

# Create tables
Base.metadata.create_all(bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize with default data if empty
def init_db():
    db = SessionLocal()
    if db.query(Club).count() == 0:
        # Create default club
        club = Club(name="Mergington High School")
        db.add(club)
        db.commit()
        db.refresh(club)

        # Create events
        events_data = [
            {"name": "Chess Club", "description": "Learn strategies and compete in chess tournaments", "schedule": "Fridays, 3:30 PM - 5:00 PM", "max_participants": 12},
            {"name": "Programming Class", "description": "Learn programming fundamentals and build software projects", "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM", "max_participants": 20},
            {"name": "Gym Class", "description": "Physical education and sports activities", "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM", "max_participants": 30},
            {"name": "Soccer Team", "description": "Join the school soccer team and compete in matches", "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM", "max_participants": 22},
            {"name": "Basketball Team", "description": "Practice and play basketball with the school team", "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM", "max_participants": 15},
            {"name": "Art Club", "description": "Explore your creativity through painting and drawing", "schedule": "Thursdays, 3:30 PM - 5:00 PM", "max_participants": 15},
            {"name": "Drama Club", "description": "Act, direct, and produce plays and performances", "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM", "max_participants": 20},
            {"name": "Math Club", "description": "Solve challenging problems and participate in math competitions", "schedule": "Tuesdays, 3:30 PM - 4:30 PM", "max_participants": 10},
            {"name": "Debate Team", "description": "Develop public speaking and argumentation skills", "schedule": "Fridays, 4:00 PM - 5:30 PM", "max_participants": 12}
        ]
        for event_data in events_data:
            event = Event(**event_data, club_id=club.id)
            db.add(event)
        db.commit()

        # Create students and attendances
        students_data = [
            ("michael@mergington.edu", ["Chess Club"]),
            ("daniel@mergington.edu", ["Chess Club"]),
            ("emma@mergington.edu", ["Programming Class"]),
            ("sophia@mergington.edu", ["Programming Class"]),
            ("john@mergington.edu", ["Gym Class"]),
            ("olivia@mergington.edu", ["Gym Class"]),
            ("liam@mergington.edu", ["Soccer Team"]),
            ("noah@mergington.edu", ["Soccer Team"]),
            ("ava@mergington.edu", ["Basketball Team"]),
            ("mia@mergington.edu", ["Basketball Team"]),
            ("amelia@mergington.edu", ["Art Club"]),
            ("harper@mergington.edu", ["Art Club"]),
            ("ella@mergington.edu", ["Drama Club"]),
            ("scarlett@mergington.edu", ["Drama Club"]),
            ("james@mergington.edu", ["Math Club"]),
            ("benjamin@mergington.edu", ["Math Club"]),
            ("charlotte@mergington.edu", ["Debate Team"]),
            ("henry@mergington.edu", ["Debate Team"])
        ]
        for email, events in students_data:
            student = Student(email=email)
            db.add(student)
            db.commit()
            db.refresh(student)
            for event_name in events:
                event = db.query(Event).filter(Event.name == event_name).first()
                if event:
                    attendance = Attendance(event_id=event.id, student_id=student.id)
                    db.add(attendance)
        db.commit()
    db.close()

init_db()


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities(db: Session = Depends(get_db)):
    events = db.query(Event).all()
    activities = {}
    for event in events:
        participants = [attendance.student.email for attendance in event.attendances]
        activities[event.name] = {
            "description": event.description,
            "schedule": event.schedule,
            "max_participants": event.max_participants,
            "participants": participants
        }
    return activities


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str, db: Session = Depends(get_db)):
    """Sign up a student for an activity"""
    # Get the event
    event = db.query(Event).filter(Event.name == activity_name).first()
    if not event:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get or create student
    student = db.query(Student).filter(Student.email == email).first()
    if not student:
        student = Student(email=email)
        db.add(student)
        db.commit()
        db.refresh(student)

    # Check if already signed up
    existing = db.query(Attendance).filter(Attendance.event_id == event.id, Attendance.student_id == student.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Student is already signed up")

    # Check max participants
    if len(event.attendances) >= event.max_participants:
        raise HTTPException(status_code=400, detail="Activity is full")

    # Add attendance
    attendance = Attendance(event_id=event.id, student_id=student.id)
    db.add(attendance)
    db.commit()
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str, db: Session = Depends(get_db)):
    """Unregister a student from an activity"""
    # Get the event
    event = db.query(Event).filter(Event.name == activity_name).first()
    if not event:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get student
    student = db.query(Student).filter(Student.email == email).first()
    if not student:
        raise HTTPException(status_code=400, detail="Student not found")

    # Get attendance
    attendance = db.query(Attendance).filter(Attendance.event_id == event.id, Attendance.student_id == student.id).first()
    if not attendance:
        raise HTTPException(status_code=400, detail="Student is not signed up for this activity")

    # Remove attendance
    db.delete(attendance)
    db.commit()
    return {"message": f"Unregistered {email} from {activity_name}"}
