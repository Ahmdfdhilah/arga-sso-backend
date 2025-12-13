from typing import List
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    APP_NAME: str = "arga-sso-service-v2"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_PREFIX: str = "/api/v1"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RUN_MIGRATIONS: bool = False

    # Database
    DATABASE_URL: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/arga_sso_v2"
    )

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT (RS256 Asymmetric)
    JWT_PRIVATE_KEY_PATH: str = "./jwt_private.pem"
    JWT_PUBLIC_KEY_PATH: str = "./jwt_public.pem"
    JWT_ALGORITHM: str = "RS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 60
    MAX_ACTIVE_SESSIONS: int = 5

    # Firebase
    FIREBASE_PROJECT_ID: str = ""
    FIREBASE_CREDENTIALS_PATH: str = "./firebase-adminsdk.json"

    # OAuth2 Google
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/login/oauth2/google/callback"
    GOOGLE_OAUTH_SCOPES: List[str] = [
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
    ]
    # Google OAuth2 Endpoints
    GOOGLE_AUTHORIZATION_ENDPOINT: str = "https://accounts.google.com/o/oauth2/v2/auth"
    GOOGLE_TOKEN_ENDPOINT: str = "https://oauth2.googleapis.com/token"
    GOOGLE_USERINFO_ENDPOINT: str = "https://www.googleapis.com/oauth2/v2/userinfo"
    GOOGLE_OPENID_CONFIG_URL: str = "https://accounts.google.com/.well-known/openid-configuration"

    # gRPC
    GRPC_HOST: str = "0.0.0.0"
    GRPC_PORT: int = 50051

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]

    # GCP Storage
    GCP_BUCKET_NAME: str = ""
    GCP_CREDENTIALS_PATH: str = "./app/credentials/gcp/credentials-gcp.json"

    # File Upload Settings
    MAX_IMAGE_SIZE: int = 5 * 1024 * 1024  # 5 MB
    MAX_DOCUMENT_SIZE: int = 10 * 1024 * 1024  # 10 MB
    MAX_VIDEO_SIZE: int = 50 * 1024 * 1024  # 50 MB

    ALLOWED_IMAGE_TYPES: set = {
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/webp",
    }
    ALLOWED_DOCUMENT_TYPES: set = {
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }
    ALLOWED_VIDEO_TYPES: set = {
        "video/mp4",
        "video/mpeg",
        "video/quicktime",
        "video/webm",
    }

    # Super Admin Seeder
    SUPERADMIN_EMAIL: str = "superadmin@arga.com"
    SUPERADMIN_PASSWORD: str = "SuperAdmin123!"
    SUPERADMIN_NAME: str = "Super Admin"
    SUPERADMIN_PHONE: str = "+6281234567890"

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
