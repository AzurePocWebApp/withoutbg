"""withoutbg: AI-powered background removal with local and cloud options."""

from .__version__ import __version__
from .api import StudioAPI
from .core import WithoutBG
from .exceptions import APIError, ModelNotFoundError, WithoutBGError
from .models import OpenSourceModel

__all__ = [
    "WithoutBG",
    "OpenSourceModel",
    "StudioAPI",
    "WithoutBGError",
    "ModelNotFoundError",
    "APIError",
    "__version__",
]
