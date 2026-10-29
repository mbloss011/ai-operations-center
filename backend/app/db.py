"""PostgreSQL via SQLAlchemy; SQLite fallback for local dev only.
Tables: workflows (graph JSON), runs (status + node outputs), artifacts.
"""
import os, json
from sqlalchemy import create_engine, Column, String, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
import datetime
URL = os.environ.get("DATABASE_URL", "sqlite:///./data/aioc.db")
if URL.startswith("sqlite"):
    os.makedirs("./data", exist_ok=True)
engine = create_engine(URL, future=True)
Session = sessionmaker(bind=engine)
Base = declarative_base()
class Workflow(Base):
    __tablename__ = "workflows"
    id = Column(String, primary_key=True); name = Column(String); graph_json = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
class Run(Base):
    __tablename__ = "runs"
    id = Column(String, primary_key=True); workflow_id = Column(String); status = Column(String, default="pending")
    outputs_json = Column(Text, default="{}"); created_at = Column(DateTime, default=datetime.datetime.utcnow)
def init_db():
    Base.metadata.create_all(engine)
