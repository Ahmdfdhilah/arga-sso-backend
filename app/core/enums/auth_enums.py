from enum import Enum


class AuthProvider(str, Enum):
    """Authentication provider types."""

    FIREBASE = "firebase"
    GOOGLE = "google"
    APPLE = "apple"
    EMAIL = "email"
    PHONE = "phone"
    GITHUB = "github"
