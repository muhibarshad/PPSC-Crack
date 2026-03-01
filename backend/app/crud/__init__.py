"""PPSC Crack — CRUD Helpers.

Centralised re-exports so callers can do::

    from app.crud import crud_user, crud_paper, crud_question
"""

from app.crud.base import CRUDBase
from app.crud.crud_job_type import crud_job_type
from app.crud.crud_topic import crud_topic
from app.crud.crud_paper import crud_paper
from app.crud.crud_question import crud_question
from app.crud.crud_topic_frequency import crud_topic_frequency
from app.crud.crud_pattern_snapshot import crud_pattern_snapshot
from app.crud.crud_current_affair import crud_current_affair
from app.crud.crud_user import crud_user
from app.crud.crud_admin_note import crud_admin_note
from app.crud.crud_prediction import crud_prediction
from app.crud.crud_email import crud_email_preference, crud_email_log

__all__ = [
    "CRUDBase",
    "crud_job_type",
    "crud_topic",
    "crud_paper",
    "crud_question",
    "crud_topic_frequency",
    "crud_pattern_snapshot",
    "crud_current_affair",
    "crud_user",
    "crud_admin_note",
    "crud_prediction",
    "crud_email_preference",
    "crud_email_log",
]
