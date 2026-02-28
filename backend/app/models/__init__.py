"""PPSC Crack — SQLAlchemy ORM Models.

Import order matters: independent tables first, then FK-dependent tables.
"""

from app.models.job_type import JobType  # noqa: F401
from app.models.topic import Topic  # noqa: F401
from app.models.paper import Paper  # noqa: F401
from app.models.question import Question  # noqa: F401
from app.models.topic_frequency import TopicFrequencyByJob  # noqa: F401
from app.models.pattern_snapshot import PatternSnapshot  # noqa: F401
from app.models.current_affair import CurrentAffairsItem  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.admin_note import AdminNote  # noqa: F401
from app.models.prediction import Prediction  # noqa: F401
