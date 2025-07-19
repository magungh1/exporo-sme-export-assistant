# Export Dashboard Architecture

## Application Flow Diagram

```mermaid
graph TB
    A[Application Start] --> B[Initialize Session State]
    B --> C[Load Page Configuration]
    C --> D[Current Page Router]
    
    D --> E[Dashboard]
    D --> F[Business Chat]
    D --> G[Product Chat]
    
    E --> H[Sidebar Navigation]
    E --> I[Product Details Card]
    E --> J[Export Readiness Chart]
    E --> K[Country Recommendations]
    E --> L[Progress Steps]
    
    L --> M[Step 1: Product Quality]
    L --> N[Step 2: Sales Strategy]
    L --> O[Step 3: Distribution]
    L --> P[Step 4: Legal Documents]
    
    M --> Q[Product Consultation Button]
    N --> R[Business Consultation Button]
    
    Q --> G
    R --> F
    
    F --> S[Business Profiling Chat]
    G --> T[Product Assessment Chat]
    
    S --> U[Gemini API - Business Profiling]
    T --> V[Gemini API - Product Assessment]
    
    U --> W[Extract Business Data]
    V --> X[Extract Product Data]
    
    W --> Y[Business Profile JSON]
    X --> Z[Product Assessment JSON]
    
    H --> AA[Navigate to Dashboard]
    H --> AB[Navigate to Business Chat]
    H --> AC[Navigate to Product Chat]
    H --> AD[Logout]
    
    AA --> E
    AB --> F
    AC --> G
    
    subgraph "Session State"
        AE[current_page]
        AF[consultation_type]
        AG[messages]
        AH[user_id]
        AI[extracted_business_data]
        AJ[extracted_product_data]
    end
    
    subgraph "Chat Components"
        AK[Chat Input with File Upload]
        AL[Message Display]
        AM[Image Processing]
        AN[Response Generation]
    end
    
    subgraph "Data Extraction"
        AO[Business Profiling Prompt]
        AP[Product Assessment Prompt]
        AQ[Gemini API Integration]
        AR[JSON Data Storage]
    end
```

## Database Implementation for User Data

### Current State
The application currently uses Streamlit's session state to store user data temporarily. This data is lost when the session ends.

### Proposed Database Architecture

```mermaid
erDiagram
    USERS {
        uuid user_id PK
        string username
        string email
        string full_name
        timestamp created_at
        timestamp updated_at
        string status
    }
    
    BUSINESS_PROFILES {
        uuid profile_id PK
        uuid user_id FK
        string company_name
        string product_name
        string product_description
        string unique_features
        integer production_capacity
        string production_unit
        string production_timeframe
        string product_category
        string production_city
        string production_province
        string production_country
        string business_background
        string conversation_language
        timestamp created_at
        timestamp updated_at
    }
    
    PRODUCT_ASSESSMENTS {
        uuid assessment_id PK
        uuid user_id FK
        string product_type
        string product_name
        string description
        string dimensions
        string target_market
        string product_category
        json raw_materials
        json certifications_required
        json compliance_gaps
        json recommendations
        timestamp created_at
        timestamp updated_at
    }
    
    CHAT_SESSIONS {
        uuid session_id PK
        uuid user_id FK
        string consultation_type
        timestamp started_at
        timestamp ended_at
        string status
    }
    
    CHAT_MESSAGES {
        uuid message_id PK
        uuid session_id FK
        string role
        text content
        json images
        timestamp created_at
    }
    
    EXPORT_PROGRESS {
        uuid progress_id PK
        uuid user_id FK
        string step_name
        string step_category
        boolean completed
        timestamp completed_at
        json step_data
        timestamp created_at
        timestamp updated_at
    }
    
    USERS ||--o{ BUSINESS_PROFILES : has
    USERS ||--o{ PRODUCT_ASSESSMENTS : has
    USERS ||--o{ CHAT_SESSIONS : has
    USERS ||--o{ EXPORT_PROGRESS : has
    CHAT_SESSIONS ||--o{ CHAT_MESSAGES : contains
```

### Implementation Steps

#### 1. Database Setup

```python
# database/models.py
from sqlalchemy import create_engine, Column, String, Integer, Boolean, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import sessionmaker, relationship
import uuid
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = Column(String(20), default='active')
    
    # Relationships
    business_profiles = relationship("BusinessProfile", back_populates="user")
    product_assessments = relationship("ProductAssessment", back_populates="user")
    chat_sessions = relationship("ChatSession", back_populates="user")
    export_progress = relationship("ExportProgress", back_populates="user")

class BusinessProfile(Base):
    __tablename__ = 'business_profiles'
    
    profile_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id'))
    company_name = Column(String(100))
    product_name = Column(String(100))
    product_description = Column(Text)
    unique_features = Column(Text)
    production_capacity = Column(Integer)
    production_unit = Column(String(50))
    production_timeframe = Column(String(50))
    product_category = Column(String(100))
    production_city = Column(String(100))
    production_province = Column(String(100))
    production_country = Column(String(100), default='Indonesia')
    business_background = Column(Text)
    conversation_language = Column(String(50), default='Indonesian')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="business_profiles")

class ProductAssessment(Base):
    __tablename__ = 'product_assessments'
    
    assessment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id'))
    product_type = Column(String(100))
    product_name = Column(String(100))
    description = Column(Text)
    dimensions = Column(String(100))
    target_market = Column(String(100))
    product_category = Column(String(100))
    raw_materials = Column(JSON)
    certifications_required = Column(JSON)
    compliance_gaps = Column(JSON)
    recommendations = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="product_assessments")

class ChatSession(Base):
    __tablename__ = 'chat_sessions'
    
    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id'))
    consultation_type = Column(String(50))
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime)
    status = Column(String(20), default='active')
    
    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session")

class ChatMessage(Base):
    __tablename__ = 'chat_messages'
    
    message_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey('chat_sessions.session_id'))
    role = Column(String(20))  # 'user' or 'assistant'
    content = Column(Text)
    images = Column(JSON)  # Store image metadata and base64 data
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")

class ExportProgress(Base):
    __tablename__ = 'export_progress'
    
    progress_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id'))
    step_name = Column(String(100))
    step_category = Column(String(50))  # 'product_quality', 'sales_strategy', etc.
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime)
    step_data = Column(JSON)  # Store step-specific data
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="export_progress")
```

#### 2. Database Connection and Session Management

```python
# database/connection.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base
import os

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost/export_dashboard')

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

#### 3. Data Access Layer

```python
# database/repository.py
from sqlalchemy.orm import Session
from database.models import User, BusinessProfile, ProductAssessment, ChatSession, ChatMessage, ExportProgress
from typing import Optional, List
import uuid

class UserRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create_user(self, user_data: dict) -> User:
        user = User(**user_data)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def get_user(self, user_id: uuid.UUID) -> Optional[User]:
        return self.db.query(User).filter(User.user_id == user_id).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

class BusinessProfileRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create_or_update_profile(self, user_id: uuid.UUID, profile_data: dict) -> BusinessProfile:
        existing_profile = self.db.query(BusinessProfile).filter(
            BusinessProfile.user_id == user_id
        ).first()
        
        if existing_profile:
            for key, value in profile_data.items():
                setattr(existing_profile, key, value)
            profile = existing_profile
        else:
            profile = BusinessProfile(user_id=user_id, **profile_data)
            self.db.add(profile)
        
        self.db.commit()
        self.db.refresh(profile)
        return profile
    
    def get_profile(self, user_id: uuid.UUID) -> Optional[BusinessProfile]:
        return self.db.query(BusinessProfile).filter(
            BusinessProfile.user_id == user_id
        ).first()

class ProductAssessmentRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create_or_update_assessment(self, user_id: uuid.UUID, assessment_data: dict) -> ProductAssessment:
        existing_assessment = self.db.query(ProductAssessment).filter(
            ProductAssessment.user_id == user_id
        ).first()
        
        if existing_assessment:
            for key, value in assessment_data.items():
                setattr(existing_assessment, key, value)
            assessment = existing_assessment
        else:
            assessment = ProductAssessment(user_id=user_id, **assessment_data)
            self.db.add(assessment)
        
        self.db.commit()
        self.db.refresh(assessment)
        return assessment
    
    def get_assessment(self, user_id: uuid.UUID) -> Optional[ProductAssessment]:
        return self.db.query(ProductAssessment).filter(
            ProductAssessment.user_id == user_id
        ).first()

class ChatRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create_session(self, user_id: uuid.UUID, consultation_type: str) -> ChatSession:
        session = ChatSession(user_id=user_id, consultation_type=consultation_type)
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session
    
    def add_message(self, session_id: uuid.UUID, role: str, content: str, images: dict = None) -> ChatMessage:
        message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            images=images
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message
    
    def get_session_messages(self, session_id: uuid.UUID) -> List[ChatMessage]:
        return self.db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at).all()
```

#### 4. Integration with Streamlit App

```python
# Modified sections for export_dashboard.py

# Add at the top of the file
from database.connection import get_db
from database.repository import UserRepository, BusinessProfileRepository, ProductAssessmentRepository, ChatRepository
from database.models import User

# Authentication and user management
def get_or_create_user(email: str, username: str, full_name: str) -> User:
    db = next(get_db())
    user_repo = UserRepository(db)
    
    # Try to get existing user
    user = user_repo.get_user_by_email(email)
    if not user:
        user = user_repo.create_user({
            'email': email,
            'username': username,
            'full_name': full_name
        })
    return user

# Modified session state initialization
def initialize_user_session():
    if 'user' not in st.session_state:
        # In a real app, you'd get this from authentication
        user = get_or_create_user(
            email="user@example.com",
            username="user123",
            full_name="Sample User"
        )
        st.session_state.user = user
        st.session_state.user_id = str(user.user_id)

# Modified data persistence functions
def save_business_profile(user_id: str, profile_data: dict):
    db = next(get_db())
    profile_repo = BusinessProfileRepository(db)
    profile_repo.create_or_update_profile(uuid.UUID(user_id), profile_data)

def load_business_profile(user_id: str) -> dict:
    db = next(get_db())
    profile_repo = BusinessProfileRepository(db)
    profile = profile_repo.get_profile(uuid.UUID(user_id))
    
    if profile:
        return {
            'company_name': profile.company_name,
            'product_name': profile.product_name,
            'product_description': profile.product_description,
            # ... other fields
        }
    return {}

def save_product_assessment(user_id: str, assessment_data: dict):
    db = next(get_db())
    assessment_repo = ProductAssessmentRepository(db)
    assessment_repo.create_or_update_assessment(uuid.UUID(user_id), assessment_data)

def load_product_assessment(user_id: str) -> dict:
    db = next(get_db())
    assessment_repo = ProductAssessmentRepository(db)
    assessment = assessment_repo.get_assessment(uuid.UUID(user_id))
    
    if assessment:
        return {
            'product_type': assessment.product_type,
            'product_name': assessment.product_name,
            'description': assessment.description,
            # ... other fields
        }
    return {}
```

#### 5. Environment Configuration

```python
# .env file
DATABASE_URL=postgresql://username:password@localhost:5432/export_dashboard
GEMINI_API_KEY=your_gemini_api_key_here
```

#### 6. Dependencies

```toml
# Add to pyproject.toml
[tool.poetry.dependencies]
sqlalchemy = "^2.0.0"
psycopg2-binary = "^2.9.0"
alembic = "^1.12.0"
python-dotenv = "^1.0.0"
```

### Migration Strategy

1. **Phase 1**: Set up database schema and models
2. **Phase 2**: Implement data repositories and connection management
3. **Phase 3**: Integrate with existing Streamlit app
4. **Phase 4**: Add user authentication and session management
5. **Phase 5**: Implement data migration from session state to database
6. **Phase 6**: Add data backup and recovery mechanisms

### Benefits of Database Implementation

1. **Persistent Data**: User data survives session restarts
2. **Scalability**: Can handle multiple concurrent users
3. **Data Analytics**: Historical data analysis and insights
4. **Backup & Recovery**: Data protection and disaster recovery
5. **User Management**: Proper user authentication and authorization
6. **Audit Trail**: Track user interactions and progress over time