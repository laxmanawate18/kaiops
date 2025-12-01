"""
SQLAlchemy ORM Models for All SRE Agent Data

Replaces MongoDB collections with PostgreSQL tables:
- applications
- users
- teams
- team_assignments
- chat_sessions
- chat_messages
- feedback
- training_dataset
- evaluation_dataset
- user_permissions
- team_permissions
- application_metadata
"""
from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text, Float, 
    ForeignKey, Table, Index, JSON, Enum, UniqueConstraint,
    TIMESTAMP, create_engine
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
import enum

Base = declarative_base()


# ==================== Enums ====================

class UserRoleEnum(str, enum.Enum):
    """User role enumeration."""
    ADMIN = "admin"
    TEAM_LEAD = "team_lead"
    USER = "user"


class ApplicationStatusEnum(str, enum.Enum):
    """Application status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    SUSPENDED = "suspended"


class FeedbackStatusEnum(str, enum.Enum):
    """Feedback status enumeration."""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    RECLASSIFIED = "RECLASSIFIED"


class FeedbackTypeEnum(str, enum.Enum):
    """Feedback type enumeration."""
    THUMBS_UP = "THUMBS_UP"
    THUMBS_DOWN = "THUMBS_DOWN"
    COPY = "COPY"
    REWRITE = "REWRITE"
    FEATURE_REQUEST = "FEATURE_REQUEST"


class DatasetTypeEnum(str, enum.Enum):
    """Dataset type enumeration."""
    TRAINING = "training"
    EVALUATION = "evaluation"


class MessageSenderEnum(str, enum.Enum):
    """Message sender type enumeration."""
    USER = "USER"
    ASSISTANT = "ASSISTANT"
    SYSTEM = "SYSTEM"


# ==================== Association Tables ====================

team_users_association = Table(
    'team_users_association',
    Base.metadata,
    Column('user_id', String(255), ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('team_id', String(255), ForeignKey('teams.id', ondelete='CASCADE'), primary_key=True),
    Column('is_team_lead', Boolean, default=False),
    Column('assigned_at', DateTime, default=datetime.now),
    Index('idx_team_users_user', 'user_id'),
    Index('idx_team_users_team', 'team_id'),
)


# ==================== USERS TABLE ====================

class User(Base):
    """User accounts for authentication."""
    __tablename__ = "users"
    
    id = Column(String(255), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(Enum(UserRoleEnum), nullable=False, default=UserRoleEnum.USER)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    teams = relationship(
        "Team",
        secondary=team_users_association,
        back_populates="users",
        lazy="select"
    )
    applications = relationship("Application", back_populates="owner", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")
    feedback = relationship("Feedback", back_populates="user", cascade="all, delete-orphan")
    permissions = relationship("UserPermission", back_populates="user", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_users_username', 'username'),
        Index('idx_users_email', 'email'),
        Index('idx_users_active', 'is_active'),
    )


# ==================== TEAMS TABLE ====================

class Team(Base):
    """Team management for RBAC."""
    __tablename__ = "teams"
    
    id = Column(String(255), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    users = relationship(
        "User",
        secondary=team_users_association,
        back_populates="teams",
        lazy="select"
    )
    permissions = relationship("TeamPermission", back_populates="team", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_teams_name', 'name'),
        Index('idx_teams_active', 'is_active'),
    )


# ==================== APPLICATIONS TABLE ====================

class Application(Base):
    """SRE-enabled application registrations."""
    __tablename__ = "applications"
    
    id = Column(String(255), primary_key=True, default=lambda: str(uuid.uuid4()))
    application_name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    application_owner = Column(String(255), ForeignKey('users.id'), nullable=False)
    status = Column(Enum(ApplicationStatusEnum), default=ApplicationStatusEnum.ACTIVE, index=True)
    
    # Cloud Provider IDs
    cloud_provider = Column(String(50), default="azure")  # azure, aws, gcp
    gcp_project_id = Column(String(255))
    aws_account_id = Column(String(255))
    azure_subscription_id = Column(String(255))
    
    # Integration Details
    github_repo = Column(String(255))
    gke_cluster_name = Column(String(255))
    argocd_app_name = Column(String(255))
    grafana_dashboard = Column(String(255))
    namespace = Column(String(255))
    
    # Metadata
    tags = Column(JSON, default=[])  # Array of tags
    created_by = Column(String(255))  # User ID who created (no FK to avoid relationship conflicts)
    updated_by = Column(String(255))  # User ID who updated (no FK to avoid relationship conflicts)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    owner = relationship("User", back_populates="applications")
    app_metadata = relationship("ApplicationMetadata", back_populates="application", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_app_name', 'application_name'),
        Index('idx_app_status', 'status'),
        Index('idx_app_owner', 'application_owner'),
        Index('idx_app_gcp_project', 'gcp_project_id'),
        Index('idx_app_aws_account', 'aws_account_id'),
        Index('idx_app_azure_sub', 'azure_subscription_id'),
    )


# ==================== APPLICATION METADATA TABLE ====================

class ApplicationMetadata(Base):
    """Extended metadata for applications."""
    __tablename__ = "application_metadata"
    
    id = Column(String(255), primary_key=True, default=lambda: str(uuid.uuid4()))
    application_id = Column(String(255), ForeignKey('applications.id', ondelete='CASCADE'), nullable=False)
    app_name = Column(String(255), nullable=False, index=True)
    team = Column(String(255))
    environment = Column(String(100))  # dev, staging, prod
    metadata_json = Column(JSON)  # Flexible storage for integration configs
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    application = relationship("Application", back_populates="app_metadata")
    
    __table_args__ = (
        Index('idx_metadata_app_id', 'application_id'),
        Index('idx_metadata_app_name', 'app_name'),
        Index('idx_metadata_team', 'team'),
    )


# ==================== CHAT SESSIONS TABLE ====================

class ChatSession(Base):
    """Chat session management."""
    __tablename__ = "chat_sessions"
    
    id = Column(String(255), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(255), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    name = Column(String(255), default="Chat Session")
    is_active = Column(Boolean, default=True)
    message_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    last_modified = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    metadata_json = Column(JSON, default={})
    
    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_chat_session_user', 'user_id'),
        Index('idx_chat_session_active', 'is_active'),
        Index('idx_chat_session_created', 'created_at'),
    )


# ==================== CHAT MESSAGES TABLE ====================

class ChatMessage(Base):
    """Chat messages for user-isolated chat history."""
    __tablename__ = "chat_messages"
    
    id = Column(String(255), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(255), ForeignKey('chat_sessions.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(String(255), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    sender = Column(Enum(MessageSenderEnum), nullable=False)
    text = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.now, nullable=False, index=True)
    metadata_json = Column(JSON, default={})
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")
    
    __table_args__ = (
        Index('idx_chat_msg_session', 'session_id'),
        Index('idx_chat_msg_user', 'user_id'),
        Index('idx_chat_msg_timestamp', 'timestamp'),
    )


# ==================== FEEDBACK TABLE ====================

class Feedback(Base):
    """Feedback for AI response improvement."""
    __tablename__ = "feedback"
    
    id = Column(String(255), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(255), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    feedback_type = Column(Enum(FeedbackTypeEnum), nullable=False)
    status = Column(Enum(FeedbackStatusEnum), default=FeedbackStatusEnum.PENDING, index=True)
    content = Column(Text, nullable=False)
    rating = Column(Integer)  # 1-5 star rating
    related_response_id = Column(String(255))  # Reference to what this feedback is about
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    metadata_json = Column(JSON, default={})
    
    # Relationships
    user = relationship("User", back_populates="feedback")
    
    __table_args__ = (
        Index('idx_feedback_user', 'user_id'),
        Index('idx_feedback_status', 'status'),
        Index('idx_feedback_type', 'feedback_type'),
        Index('idx_feedback_created', 'created_at'),
    )


# ==================== TRAINING DATASET TABLE ====================

class TrainingDataset(Base):
    """Training data entries for ML model improvement."""
    __tablename__ = "training_dataset"
    
    id = Column(String(255), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(255), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    input_text = Column(Text, nullable=False)
    output_text = Column(Text, nullable=False)
    score = Column(Float)
    category = Column(String(100))
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    metadata_json = Column(JSON, default={})
    
    __table_args__ = (
        Index('idx_training_user', 'user_id'),
        Index('idx_training_category', 'category'),
        Index('idx_training_created', 'created_at'),
    )


# ==================== EVALUATION DATASET TABLE ====================

class EvaluationDataset(Base):
    """Evaluation data entries for model performance testing."""
    __tablename__ = "evaluation_dataset"
    
    id = Column(String(255), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(255), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    input_text = Column(Text, nullable=False)
    expected_output = Column(Text, nullable=False)
    actual_output = Column(Text)
    accuracy_score = Column(Float)
    category = Column(String(100))
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    metadata_json = Column(JSON, default={})
    
    __table_args__ = (
        Index('idx_evaluation_user', 'user_id'),
        Index('idx_evaluation_category', 'category'),
        Index('idx_evaluation_created', 'created_at'),
    )


# ==================== PERMISSIONS TABLES ====================

class UserPermission(Base):
    """User-level permissions."""
    __tablename__ = "user_permissions"
    
    id = Column(String(255), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(255), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    resource = Column(String(255), nullable=False)  # e.g., "applications", "teams"
    action = Column(String(100), nullable=False)  # e.g., "create", "read", "update", "delete"
    granted = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="permissions")
    
    __table_args__ = (
        Index('idx_user_perm_user', 'user_id'),
        Index('idx_user_perm_resource', 'resource'),
    )


class TeamPermission(Base):
    """Team-level permissions."""
    __tablename__ = "team_permissions"
    
    id = Column(String(255), primary_key=True, default=lambda: str(uuid.uuid4()))
    team_id = Column(String(255), ForeignKey('teams.id', ondelete='CASCADE'), nullable=False, index=True)
    resource = Column(String(255), nullable=False)
    action = Column(String(100), nullable=False)
    granted = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    
    # Relationships
    team = relationship("Team", back_populates="permissions")
    
    __table_args__ = (
        Index('idx_team_perm_team', 'team_id'),
        Index('idx_team_perm_resource', 'resource'),
    )
