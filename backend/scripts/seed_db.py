import sys
from pathlib import Path

# Add the 'app' directory to the Python path so imports work correctly
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.db.session import SessionLocal, engine
from app.db.base import Base
from app.db.models.user import User
from app.db.models.document import Document
from app.db.models.quiz import Quiz, QuizQuestion
from app.db.models.flashcard import Flashcard
from app.db.models.study_plan import StudyPlan, StudyTask
from app.utils.security import get_password_hash
from datetime import datetime, timezone, timedelta

def reset_db():
    print("Dropping existing tables...")
    Base.metadata.drop_all(bind=engine)
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)

def seed():
    db = SessionLocal()
    try:
        # 1. Create a Test User
        print("Creating User...")
        test_user = User(
            email="alice@studyos.com",
            hashed_password=get_password_hash("password123"),
            full_name="Alice Student",
            is_active=True
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        user_id = test_user.id

        # 2. Add Documents
        print("Creating Documents...")
        doc1 = Document(
            user_id=user_id,
            title="Introduction to Biology",
            file_type="PDF",
            file_path="/mock/path/biology.pdf",
            status="processed"
        )
        doc2 = Document(
            user_id=user_id,
            title="Computer Science 101 Syllabus",
            file_type="PDF",
            file_path="/mock/path/cs_syllabus.pdf",
            status="processed"
        )
        db.add_all([doc1, doc2])
        db.commit()
        db.refresh(doc1)

        # 3. Add Flashcards
        print("Creating Flashcards...")
        fc1 = Flashcard(
            user_id=user_id,
            document_id=doc1.id,
            front="What is the powerhouse of the cell?",
            back="Mitochondria",
            interval=30, # Mastered
            repetition=5,
            ease_factor=2.6,
            next_review=datetime.now(timezone.utc) + timedelta(days=30)
        )
        fc2 = Flashcard(
            user_id=user_id,
            document_id=doc1.id,
            front="What is photosynthesis?",
            back="The process by which plants use sunlight to synthesize foods from carbon dioxide and water.",
            interval=1, # Learning
            repetition=1,
            ease_factor=2.0,
            next_review=datetime.now(timezone.utc) - timedelta(days=1) # Due for review
        )
        db.add_all([fc1, fc2])

        # 4. Add Quizzes
        print("Creating Quiz...")
        quiz = Quiz(
            user_id=user_id,
            document_id=doc1.id,
            title="Biology Basics Quiz",
            score=80.0
        )
        db.add(quiz)
        db.commit()
        db.refresh(quiz)

        q1 = QuizQuestion(
            quiz_id=quiz.id,
            question="Which organelle is responsible for respiration?",
            options='["Nucleus", "Ribosome", "Mitochondria", "Golgi"]',
            correct_answer="Mitochondria",
            explanation="Mitochondria produce energy via respiration."
        )
        db.add(q1)

        # 5. Add Study Plan
        print("Creating Study Plan...")
        plan = StudyPlan(
            user_id=user_id,
            title="Final Exam Prep",
            target_date=datetime.now(timezone.utc) + timedelta(days=14)
        )
        db.add(plan)
        db.commit()
        db.refresh(plan)

        task1 = StudyTask(
            plan_id=plan.id,
            title="Review Biology Notes",
            due_date=datetime.now(timezone.utc) + timedelta(days=2),
            completed=True
        )
        task2 = StudyTask(
            plan_id=plan.id,
            title="Take Biology Quiz",
            due_date=datetime.now(timezone.utc) + timedelta(days=5),
            completed=False
        )
        db.add_all([task1, task2])

        db.commit()
        print("Database seeding completed successfully!")

    except Exception as e:
        print(f"Error during seeding: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    reset_db()
    seed()
