"""PPSC Crack — Pydantic Schemas (Request / Response).

Re-exports every schema so callers can do:
    from app.schemas import UserResponse, PaperCreate, ...
"""

# Auth
from app.schemas.auth import (
    AuthTokenResponse,
    AuthUserInfo,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    MagicLinkRequest,
    MagicLinkResponse,
    OAuthCallbackRequest,
    OAuthURLResponse,
    RefreshResponse,
    RegisterRequest,
    RegisterResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    TokenPayload,
    UpdateProfileRequest,
    UpdateProfileResponse,
)

# Job types
from app.schemas.job_type import (
    JobTypeCreate,
    JobTypeListResponse,
    JobTypeResponse,
    JobTypeUpdate,
)

# Topics
from app.schemas.topic import (
    TopicCreate,
    TopicListResponse,
    TopicResponse,
    TopicUpdate,
)

# Papers
from app.schemas.paper import (
    PaperCreate,
    PaperListResponse,
    PaperResponse,
    PaperUpdate,
)

# Questions
from app.schemas.question import (
    QuestionCreate,
    QuestionListResponse,
    QuestionResponse,
    QuestionUpdate,
    SimilarQuestionResult,
)

# Topic frequency
from app.schemas.topic_frequency import (
    TopicFrequencyCreate,
    TopicFrequencyListResponse,
    TopicFrequencyResponse,
)

# Pattern snapshots
from app.schemas.pattern_snapshot import (
    PatternSnapshotCreate,
    PatternSnapshotListResponse,
    PatternSnapshotResponse,
)

# Pattern overview (intelligence engine)
from app.schemas.pattern_overview import (
    DueTopic,
    HighFrequencyFact,
    PatternOverviewResponse,
    RepeatQuestionSummary,
    TopicTrend,
)

# Current affairs
from app.schemas.current_affair import (
    CurrentAffairCreate,
    CurrentAffairListResponse,
    CurrentAffairResponse,
    CurrentAffairUpdate,
    CurrentAffairAdminResponse,
    CurrentAffairAdminListResponse,
    CurrentAffairManualAdd,
    CurrentAffairApprove,
)

# Users
from app.schemas.user import (
    UserAdminResponse,
    UserBrief,
    UserCreate,
    UserResponse,
    UserUpdate,
)

# Admin notes
from app.schemas.admin_note import (
    AdminNoteCreate,
    AdminNoteListResponse,
    AdminNoteResponse,
    AdminNoteUpdate,
    AdminNoteUploadResponse,
    AdminNoteProcessingResult,
)

# Predictions
from app.schemas.prediction import (
    PredictionGenerateRequest,
    PredictionUpdate,
    PredictedQuestion,
    PredictionResponse,
    PredictionListResponse,
    PredictionPublishResponse,
    PredictionSSEEvent,
    PredictionGenerateResponse,
)

__all__ = [
    # Auth
    "RegisterRequest", "RegisterResponse", "LoginRequest",
    "AuthTokenResponse", "AuthUserInfo", "RefreshResponse",
    "TokenPayload",
    "MagicLinkRequest", "MagicLinkResponse",
    "OAuthURLResponse", "OAuthCallbackRequest",
    "ForgotPasswordRequest", "ForgotPasswordResponse",
    "ResetPasswordRequest", "ResetPasswordResponse",
    "UpdateProfileRequest", "UpdateProfileResponse",
    # Job types
    "JobTypeCreate", "JobTypeUpdate", "JobTypeResponse", "JobTypeListResponse",
    "JobTypeTopicRatiosUpdate",
    # Topics
    "TopicCreate", "TopicUpdate", "TopicResponse", "TopicListResponse",
    # Papers
    "PaperCreate", "PaperUpdate", "PaperResponse", "PaperListResponse",
    # Questions
    "QuestionCreate", "QuestionUpdate", "QuestionResponse",
    "QuestionListResponse", "SimilarQuestionResult",
    # Topic frequency
    "TopicFrequencyCreate", "TopicFrequencyResponse", "TopicFrequencyListResponse",
    # Pattern snapshots
    "PatternSnapshotCreate", "PatternSnapshotResponse", "PatternSnapshotListResponse",
    # Pattern overview
    "PatternOverviewResponse", "TopicTrend", "DueTopic",
    "HighFrequencyFact", "RepeatQuestionSummary",
    # Current affairs
    "CurrentAffairCreate", "CurrentAffairUpdate",
    "CurrentAffairResponse", "CurrentAffairListResponse",
    "CurrentAffairAdminResponse", "CurrentAffairAdminListResponse",
    "CurrentAffairManualAdd", "CurrentAffairApprove",
    # Users
    "UserCreate", "UserUpdate", "UserResponse", "UserBrief", "UserAdminResponse",
    # Admin notes
    "AdminNoteCreate", "AdminNoteUpdate", "AdminNoteResponse", "AdminNoteListResponse",
    "AdminNoteUploadResponse", "AdminNoteProcessingResult",
    # Predictions
    "PredictionGenerateRequest", "PredictionUpdate", "PredictedQuestion",
    "PredictionResponse", "PredictionListResponse", "PredictionPublishResponse",
    "PredictionSSEEvent", "PredictionGenerateResponse",
]
