"""Skill engine. Importing this package registers all skills into base.REGISTRY."""

from mathkids.engine import grade2, grade3, grade4  # noqa: F401  (side-effect: registration)
from mathkids.engine.base import (
    REGISTRY,
    SEQUENCES,
    Lesson,
    Problem,
    Skill,
    register,
    skills_for_grade,
)

__all__ = [
    "REGISTRY",
    "SEQUENCES",
    "Lesson",
    "Problem",
    "Skill",
    "register",
    "skills_for_grade",
]
