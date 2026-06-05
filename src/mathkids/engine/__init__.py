"""Skill engine. Importing this package registers all skills into base.REGISTRY."""

from mathkids.engine import grade2, grade4  # noqa: F401  (import for side-effect: registration)
from mathkids.engine.base import (
    REGISTRY,
    Lesson,
    Problem,
    Skill,
    register,
    skills_for_grade,
)

__all__ = [
    "REGISTRY",
    "Lesson",
    "Problem",
    "Skill",
    "register",
    "skills_for_grade",
]
