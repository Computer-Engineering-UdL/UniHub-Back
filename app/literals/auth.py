from enum import Enum
from typing import Literal

TokenType = Literal["bearer", "oauth2"]


class OAuthProvider(str, Enum):
    GOOGLE = "google"
    GITHUB = "github"
