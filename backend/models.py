from sqlalchemy import Column, String, Integer, JSON, ForeignKey, Float, BigInteger, Boolean, Text
from sqlalchemy.orm import relationship
from backend.database import Base
import time
import uuid

class Session(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True, index=True)
    created_at = Column(BigInteger, default=lambda: int(time.time() * 1000))
    status = Column(String, default="active") # active, closed
    outcome = Column(String, nullable=True) # sale, no_sale
    journey_stage = Column(String, default="DISCOVERY")
    last_updated = Column(BigInteger, default=lambda: int(time.time() * 1000))

    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")
    analysis_state = relationship("AnalysisState", back_populates="session", uselist=False, cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("sessions.id"))
    role = Column(String) # user, ai, system
    content = Column(String)
    timestamp = Column(BigInteger, default=lambda: int(time.time() * 1000))
    
    # AI Metadata stored as JSON
    confidence = Column(Float, nullable=True)
    confidence_reason = Column(String, nullable=True)
    client_style = Column(String, nullable=True)
    context_needs = Column(JSON, nullable=True)
    suggested_actions = Column(JSON, nullable=True)
    
    # Feedback
    feedback = Column(String, nullable=True)
    feedback_details = Column(String, nullable=True)

    session = relationship("Session", back_populates="messages")

class AnalysisState(Base):
    __tablename__ = "analysis_states"

    session_id = Column(String, ForeignKey("sessions.id"), primary_key=True)
    
    # Storing the entire nested analysis object as JSON for flexibility
    # This matches the AnalysisState interface in types.ts
    data = Column(JSON) 
    
    last_updated = Column(BigInteger, default=lambda: int(time.time() * 1000))

    session = relationship("Session", back_populates="analysis_state")


class FeedbackLog(Base):
    """
    AI Dojo Feedback Loop - Expert Corrections & Ratings
    Used for continuous learning and model improvement.
    
    Training Data Format:
    - user_input_snapshot: The INPUT context (user's message or session summary)
    - ai_output_snapshot: The OUTPUT (AI response being rated)
    - expert_comment: The CORRECTION (what should have been said)
    """
    __tablename__ = "feedback_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("sessions.id"), nullable=True)
    
    # Which component is being rated
    # e.g., "fast_path", "slow_path_m1_dna", "slow_path_m2_indicators", etc.
    module_name = Column(String, nullable=False)
    
    # Rating: True = Like (👍), False = Dislike (👎)
    rating = Column(Boolean, nullable=False)
    
    # INPUT CONTEXT: The user's message or session context that triggered the AI output
    # For Fast Path: Last user message
    # For Slow Path: Aggregated conversation summary or last few messages
    user_input_snapshot = Column(Text, nullable=True)
    
    # OUTPUT: The AI output being rated (snapshot for training data)
    ai_output_snapshot = Column(Text, nullable=True)
    
    # CORRECTION: Expert's correction or explanation
    expert_comment = Column(Text, nullable=True)
    
    # Timestamp
    timestamp = Column(BigInteger, default=lambda: int(time.time() * 1000))
    
    # Optional: Link to specific message ID for Fast Path feedback
    message_id = Column(String, nullable=True)

    # V4.0 DOJO-REFINER: Processing flag for auto-learning
    # When True, feedback has been processed by DojoRefiner and used for improvement
    processed = Column(Boolean, default=False, nullable=False)

    # Relationship to session (optional, for querying)
    session = relationship("Session", backref="feedback_logs")
