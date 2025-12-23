# SSO Service v2 - Base Rules

## Project Structure

```bash
arga-sso-service-v2/
├── app/
│   ├── main.py                         # FastAPI entry point (clean)
│   ├── config/
│   │   ├── settings.py                 # Pydantic settings
│   │   ├── database.py                 # Async SQLAlchemy
│   │   └── redis.py                    # Redis connection
│   ├── core/
│   │   ├── exceptions/                 # AppException, client errors
│   │   ├── schemas/                    # BaseResponse, DataResponse[T]
│   │   ├── middleware/                 # ErrorHandler, Logging
│   │   ├── routers/                    # setup_routers()
│   │   ├── security/                   # JWT, Password, Firebase
│   │   └── utils/                      # datetime helpers
│   │
│   └── modules/
│       └── auth/                       # Example module
│           ├── models/
│           │   └── auth_provider.py
│           ├── schemas/
│           │   ├── requests.py         # Input DTOs
│           │   ├── responses.py        # Output DTOs
│           │   └── shared.py           # Enums, shared types
│           ├── repositories/
│           │   ├── commands/           # Write operations
│           │   └── queries/            # Read operations
│           ├── use_cases/              # One class per operation
│           │   ├── create_{entity}.py
│           │   ├── update_{entity}.py
│           │   ├── delete_{entity}.py
│           │   ├── get_{entity}.py
│           │   └── list_{entity}.py
│           ├── services/               # Lightweight orchestrators
│           ├── utils/                  # Module-specific helpers
│           ├── dependencies.py         # DI definitions
│           └── routers/
│
├── scripts/                            # Seeders, utilities
├── alembic/                            # Migrations
└── docs/
```

---

## ⚠️ Pre-Coding Checklist (WAJIB!)

**SELALU CEK DULU SEBELUM MENULIS CODE!** Checklist ini mencegah: redundancy, type errors, bugs, dan technical debt.

### ✅ Before Creating New Function/Method

- [ ] **Cek `utils/` dulu** - Apakah fungsi serupa sudah ada di module utils atau core utils?
- [ ] **Cek services lain** - Apakah logic ini sudah di-implement di service/module lain?
- [ ] **Reusability check** - Apakah logic ini akan dipakai di 2+ tempat? Jika ya, buat di utils (bukan private method)

### ✅ Before Creating New Schema

- [ ] **Cek schemas existing** - Apakah schema dengan field yang sama sudah ada?
- [ ] **Cross-module check** - Cek `auth/schemas`, `users/schemas`, dan `core/schemas`
- [ ] **Naming consistency** - Apakah naming sudah sesuai convention? (`{Resource}Response`, `{Resource}ListItemResponse`)

### ✅ Before Creating New Enum

- [ ] **Cek `app/core/enums/`** - SEMUA enum HARUS di `core/enums/`, BUKAN di schemas
- [ ] **No duplicate values** - Pastikan enum values tidak terduplikasi dengan enum lain

### ✅ Before Writing Service Logic

- [ ] **Repository exists?** - Apakah repository query/command yang dibutuhkan sudah ada?
- [ ] **Transaction handling** - Apakah operasi butuh atomic transaction?
- [ ] **Error handling** - Gunakan custom exceptions dari `app.core.exceptions`
- [ ] **Logging** - Tambahkan log untuk operasi penting (auth, create, update, delete)

### ✅ Before Writing Router Endpoint

- [ ] **Route conflict check** - Static routes (`/me`) HARUS didefinisikan SEBELUM dynamic routes (`/{id}`)
- [ ] **HTTP method** - Gunakan method yang benar (GET/POST/PATCH/DELETE)
- [ ] **Response model** - `DataResponse[{Resource}Response]` untuk detail, `DataListResponse[{Resource}ListItemResponse]` untuk list
- [ ] **Authorization** - Apakah endpoint butuh `@require_auth` atau `@require_role`?
- [ ] **Tags** - JANGAN define tags di router, define di `core/routers/routers.py`

### ✅ Type Safety Check

- [ ] **Type hints** - Semua function parameters dan return types punya type hints
- [ ] **Optional vs Required** - Field nullable gunakan `Optional[T]`, required gunakan `T`
- [ ] **Import order** - Standard library → Third-party → Local (absolute imports)
- [ ] **No Any type** - Hindari `Any`, gunakan specific types

### ✅ Code Quality Check

- [ ] **DRY principle** - Tidak ada duplicate code
- [ ] **Single responsibility** - Satu function/class = satu tanggung jawab
- [ ] **Clear naming** - Variable/function names descriptive (bukan `x`, `data`, `temp`)
- [ ] **Comments only when needed** - Code should be self-documenting

### 🚨 Common Mistakes to Avoid

| Mistake | Why Bad | Correct Approach |
|---------|---------|------------------|
| Private helper in service | Not reusable, likely duplicated elsewhere | Create public utility function |
| Duplicate schema | Type inconsistency, maintenance hell | Use shared schema or import existing |
| Enum in schemas | Not centralized, duplication across modules | Define in `app/core/enums/` |
| No type hints | Type errors at runtime | Always use type hints |
| Hardcoded values | Not configurable | Use settings or constants |
| Direct DB access in router | No business logic layer | Use service layer |
| Catching all exceptions | Masks real errors | Catch specific exceptions |

**Ingat**: 5 menit cek sekarang = menghemat 5 jam debugging nanti! 🎯

---

## Use Cases (One Class Per Operation)

**Rule**: Satu use-case class = satu operasi bisnis. Hindari monolithic service dengan banyak method.

```python
# ✅ CORRECT - Separated by operation (Use Case Pattern)
use_cases/
├── create_user.py             # CreateUserUseCase.execute()
├── update_user.py             # UpdateUserUseCase.execute()
├── delete_user.py             # DeleteUserUseCase.execute()
├── get_user.py                # GetUserUseCase.execute()
└── list_users.py              # ListUsersUseCase.execute()

# ❌ WRONG - Monolithic service
services/
└── user_service.py            # 500+ lines with everything
```

### Use Case Structure

```python
# use_cases/create_user.py
from typing import Optional
from fastapi import UploadFile

class CreateUserUseCase:
    """Use Case for creating a new user."""

    def __init__(
        self,
        queries: UserQueries,
        commands: UserCommands,
        event_publisher: Optional[EventPublisher] = None,
    ):
        self.queries = queries
        self.commands = commands
        self.event_publisher = event_publisher

    async def execute(
        self,
        data: UserCreateRequest,
        avatar_file: Optional[UploadFile] = None,
    ) -> UserResponse:
        """Execute the create user use case."""
        # 1. Validation
        # 2. Business logic
        # 3. Persistence
        # 4. Events
        return UserResponseBuilder.build(user)
```

### When to Use Use Cases vs Services

| Scenario | Use |
|----------|-----|
| CRUD operations | Use Cases (one per operation) |
| Complex multi-step operations | Use Cases |
| Stateless utilities (token, session) | Services |
| External integrations (Redis, Firebase) | Services |

---

## Services (Lightweight Orchestrators)

**Rule**: Services untuk operasi yang bukan CRUD atau butuh shared state. Jika logic spesifik untuk satu operasi, gunakan Use Case.

```python
# ✅ CORRECT - Services for specific purposes
services/
├── session_service.py         # Redis session management
├── sso_session_service.py     # SSO-specific session logic
└── firebase_auth_service.py   # Firebase integration
```

---

## Repository Pattern

**Commands** = Write (create, update, delete)  
**Queries** = Read (get, list, search)

```python
# repositories/commands/user_commands.py
class UserCommands:
    async def create(self, name: str, email: str) -> User: ...
    async def update(self, user_id: str, data: dict) -> User: ...
    async def delete(self, user_id: str) -> None: ...

# repositories/queries/user_queries.py
class UserQueries:
    async def get_by_id(self, user_id: str) -> Optional[User]: ...
    async def get_by_email(self, email: str) -> Optional[User]: ...
    async def list_all(self, skip: int, limit: int) -> list[User]: ...
```

---

## Enums (Centralized)

**Location**: `app/core/enums/` - Semua enum didefinisikan di sini untuk konsistensi dan type safety.

```bash
app/core/enums/
├── __init__.py           # Export all enums
├── user_enums.py         # UserRole, UserStatus
└── auth_enums.py         # AuthProvider
```

**Usage**:

```python
from app.core.enums import UserRole, UserStatus, AuthProvider

# Di schemas
class UserCreateRequest(BaseModel):
    role: UserRole = Field(default=UserRole.USER)
    status: UserStatus = Field(default=UserStatus.ACTIVE)

# Di services
auth_provider = await self.auth_queries.get_by_provider_user_id(
    provider=AuthProvider.GOOGLE.value,
    provider_user_id=google_id,
)

# Di authorization
require_admin = RoleChecker([UserRole.SUPERADMIN, UserRole.ADMIN])
```

**Available Enums**:

| Enum | Values |
|------|--------|
| `UserRole` | `superadmin`, `admin`, `user`, `guest` |
| `UserStatus` | `active`, `inactive`, `suspended`, `deleted` |
| `AuthProvider` | `firebase`, `google`, `apple`, `email`, `phone`, `github` |

---

## Schemas (DTOs)

| File | Purpose | Example |
|------|---------|---------|
| `requests.py` | Input validation | `LoginRequest`, `CreateUserRequest` |
| `responses.py` | Output format | `LoginResponse`, `UserResponse` |
| `shared.py` | Shared schemas between req/res | `PinPointSchema`, `BaseDataSchema` |

```python
# schemas/requests.py - Input
class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)

# schemas/responses.py - Output
class LoginResponse(BaseModel):
    access_token: str
    user: UserData

# schemas/shared.py - Shared (optional, for complex modules)
class PinPointSchema(BaseModel):
    """Shared between request and response schemas."""
    lat: float
    lon: float
```

> [!NOTE]
> `shared.py` adalah opsional. Gunakan hanya jika ada Pydantic schema yang perlu dipakai di **kedua** requests.py dan responses.py. Untuk enum, gunakan `app.core.enums`.

### Response Schemas: Detail vs List

**Rule**: Response schemas untuk **detail** (single resource) dan **list** (pagination) harus dipisah dengan naming convention yang jelas.

```python
# ✅ CORRECT - Separate schemas
# schemas/responses.py
class UserResponse(BaseModel):
    """Full detail response untuk single user (GET /users/{id})"""
    id: str
    name: str
    email: Optional[str]
    phone: Optional[str]
    avatar_url: Optional[str]
    role: UserRole
    status: UserStatus
    created_at: datetime
    updated_at: datetime
    # Include all fields and relationships

class UserListItemResponse(BaseModel):
    """Simplified response untuk list/pagination (GET /users)"""
    id: str
    name: str
    email: Optional[str]
    avatar_url: Optional[str]
    role: UserRole
    status: UserStatus
    # Only essential fields for list view
```

**Naming Convention**:

- Detail: `{Resource}Response` (e.g., `UserResponse`, `ApplicationResponse`)
- List: `{Resource}ListItemResponse` (e.g., `UserListItemResponse`, `ApplicationListItemResponse`)

**Usage in Routers**:

```python
from app.core.schemas.data import DataResponse, DataListResponse

@router.get("/{user_id}", response_model=DataResponse[UserResponse])
async def get_user(user_id: str):
    """Single user detail"""
    user = await service.get_by_id(user_id)
    return DataResponse(data=user)

@router.get("/", response_model=DataListResponse[UserListItemResponse])
async def list_users(page: int = 1, limit: int = 10):
    """Paginated user list"""
    users, total = await service.list_all(page, limit)
    return DataListResponse(
        data=users,
        pagination=PaginationMeta(page=page, limit=limit, total=total)
    )
```

**Why Separate?**

1. **Performance**: List responses tidak perlu include semua field/relationships
2. **Clarity**: Jelas mana schema untuk detail vs list
3. **Flexibility**: Mudah modify tanpa affect satu sama lain
4. **Type Safety**: FastAPI response_model validation lebih akurat

---

## Utils

**Module utils** = helpers khusus untuk module itu saja.

```python
# modules/auth/utils/token_helper.py
class TokenHelper:
    """Helper untuk create login response dengan session."""
    async def create_login_response(self, user: User) -> LoginResponse: ...
```

**Core utils** = helpers global yang dipakai semua module.

```python
# core/utils/datetime.py
def get_utc_now() -> datetime: ...
```

### Avoiding Redundant Functions (DRY Principle)

**Rule**: Sebelum membuat fungsi baru, SELALU cek dulu apakah sudah ada fungsi serupa di utils (module atau core).

**Problem**: Duplicate logic di berbagai service.

```python
# ❌ WRONG - Duplicate helper di services
# auth_service.py
class AuthService:
    def _extract_allowed_apps(self, user): ...  # Private helper

# user_service.py
class UserService:
    def _extract_allowed_apps(self, user): ...  # Duplicate logic!
```

**Solution**: Buat fungsi reusable di utils.

```python
# ✅ CORRECT - Single source of truth
# modules/auth/utils/token_helper.py
class TokenHelper:
    @staticmethod
    def extract_allowed_apps_from_user(user: User) -> tuple[List[AllowedApp], List[str]]:
        """Extract allowed apps - reusable across services."""
        allowed_apps = []
        allowed_app_codes = []
        # Logic here...
        return allowed_apps, allowed_app_codes

# auth_service.py
from app.modules.auth.utils.token_helper import TokenHelper

class AuthService:
    async def refresh_token(self, ...):
        apps, codes = TokenHelper.extract_allowed_apps_from_user(user)
```

**Best Practices**:

1. **Check Utils First**: Sebelum buat helper function baru, cek `utils/` apakah sudah ada
2. **No Private Helpers in Services**: Jika logic bisa reusable, pindahkan ke utils (bukan private method)
3. **Static Methods for Pure Functions**: Jika function tidak butuh instance state, gunakan `@staticmethod`
4. **Descriptive Names**: Utils harus punya nama yang jelas agar mudah dicari

**When to Create Utils**:

- Logic dipakai di **2+ services** → module utils
- Logic dipakai di **2+ modules** → core utils
- Builder/formatter functions → utils (bukan private methods)
- Pure functions (no side effects) → static methods in utils

---

## HTTP Methods untuk CRUD

**Rule**: Gunakan method yang sesuai dengan operasi yang dilakukan.

| Operation | HTTP Method | Use Case |
|-----------|-------------|----------|
| **Create** | `POST` | Buat resource baru |
| **Read (single)** | `GET /{id}` | Ambil satu resource |
| **Read (list)** | `GET /` | Ambil banyak resource |
| **Update (partial)** | `PATCH /{id}` | Update beberapa field (recommended) |
| **Update (full)** | `PUT /{id}` | Replace seluruh resource |
| **Delete** | `DELETE /{id}` | Hapus resource |

### PUT vs PATCH

**PUT** - Full replacement (jarang dipakai):

```python
# Client HARUS kirim SEMUA field
PUT /users/123
{
  "name": "John",
  "email": "john@example.com",
  "phone": "08123456789",
  "address": "..."
}
```

**PATCH** - Partial update (recommended):

```python
# Client hanya kirim field yang mau diubah
PATCH /users/123
{
  "email": "newemail@example.com"
}
# Field lain tetap seperti semula
```

### Contoh Implementasi

```python
# ✅ CORRECT - Konsisten pakai PATCH
@router.patch("/me")
async def update_my_profile(data: UserUpdateRequest): ...

@router.patch("/{user_id}")
async def update_user(user_id: str, data: UserUpdateRequest): ...

# ❌ WRONG - Tidak konsisten
@router.put("/me")           # Pakai PUT
async def update_my_profile(data: UserUpdateRequest): ...

@router.patch("/{user_id}")  # Pakai PATCH
async def update_user(user_id: str, data: UserUpdateRequest): ...
```

**Best Practice**: Gunakan **PATCH** untuk semua update operation kecuali memang butuh full replacement.

---

## Router Tags (OpenAPI/Swagger Groups)

**Problem**: Jangan define tags di dua tempat (router definition + include_router), karena akan muncul duplicate groups di Swagger.

```python
# ❌ WRONG - Double tags
# modules/users/routers/users.py
router = APIRouter(tags=["Users"])

# core/routers/routers.py
app.include_router(users_router, prefix="/users", tags=["User Management"])
# Result: Muncul 2 groups di Swagger! "Users" dan "User Management"
```

**Solution**: Define tags HANYA di centralized router setup.

```python
# ✅ CORRECT
# modules/users/routers/users.py
router = APIRouter()  # Tanpa tags

# core/routers/routers.py
app.include_router(users_router, prefix="/users", tags=["User Management"])
# Result: Hanya 1 group "User Management"
```

**Rule**: Tags didefinisikan di `core/routers/routers.py` saja untuk konsistensi.

---

## Router Path Conflicts

**Problem**: `/{id}` akan menangkap semua path termasuk `/me`.

```python
# ❌ WRONG - /me akan ditangkap oleh /{user_id}
@router.get("/{user_id}")
async def get_user(user_id: str): ...

@router.get("/me")       # Tidak akan pernah tercapai!
async def get_me(): ...
```

**Solution**: Definisikan static routes SEBELUM dynamic routes.

```python
# ✅ CORRECT - Static routes first
@router.get("/me")       # Definisikan dulu
async def get_me(): ...

@router.get("/{user_id}")  # Dynamic route terakhir
async def get_user(user_id: str): ...
```

---

## Dependencies (DI)

```python
# dependencies.py
from typing import Annotated
from fastapi import Depends

def get_auth_service(...) -> AuthService:
    return AuthService(...)

# Annotated type untuk reusable dependency
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
```

```python
# ✅ CORRECT - Annotated deps tanpa = Depends()
async def login(auth_service: AuthServiceDep):
    ...

# ❌ WRONG - Double Depends
async def login(auth_service: AuthServiceDep = Depends()):
    ...
```

---

## Authorization

```python
from app.core.security import require_admin, get_current_user

@router.get("/users")
async def list_users(current_user: UserData = Depends(require_admin)):
    ...

@router.get("/me")
async def get_me(current_user: UserData = Depends(get_current_user)):
    ...
```

| Role | Access |
|------|--------|
| `superadmin` | Full access |
| `admin` | Manage users |
| `user` | Own profile only |

---

## Messages

User-facing messages dalam **Bahasa Indonesia**:

```python
# ✅ Correct
message="Login berhasil"
message="User tidak ditemukan"

# ❌ Wrong
message="Login successful"
```

---

## Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Files | snake_case | `user_service.py` |
| Classes | PascalCase | `UserService` |
| Functions | snake_case | `get_user_by_id` |
| Constants | UPPER_SNAKE | `SESSION_TTL` |
| DB Tables | snake_case plural | `users` |
| API Endpoints | kebab-case | `/auth/login/email` |

---

## Running

```bash
# Install & setup
pip install -r requirements.txt
cp .env.example .env

# Migrations
alembic upgrade head

# Run
uvicorn app.main:app --reload
```

---

## GCP Storage ( File Uploads)

**Rule**: Semua file uploads (avatar, documents, dll) disimpan di **GCP private bucket** dengan signed URLs.

### Configuration

```bash
# .env
GCP_BUCKET_NAME=your-bucket-name
GCP_CREDENTIALS_PATH=./app/credentials/gcp/credentials-gcp.json
```

**Settings** (`app/config/settings.py`):

```python
# GCP Storage
GCP_BUCKET_NAME: str = ""
GCP_CREDENTIALS_PATH: str = "./app/credentials/gcp/credentials-gcp.json"

# File Upload Limits
MAX_IMAGE_SIZE: int = 5 * 1024 * 1024  # 5 MB
MAX_DOCUMENT_SIZE: int = 10 * 1024 * 1024  # 10 MB

ALLOWED_IMAGE_TYPES: set = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
ALLOWED_DOCUMENT_TYPES: set = {"application/pdf", ...}
```

### Core Utilities

**Location**: `app/core/utils/`

| File | Purpose |
|------|---------|
| `gcp_storage.py` | GCP Storage client (singleton) |
| `file_upload.py` | File validation, upload, generate signed URLs |


### Storage Structure Example

```
bucket-name/
└── users/
    └── {user_id}/
        └── avatar/
            └── {uuid}.jpg
```

**Pattern**: `{entity_type}/{entity_id}/{subfolder}/{uuid}.{ext}`

### Upload File Pattern

#### Basic Upload

```python
from app.core.utils.file_upload import upload_file_to_gcp

# Upload image
signed_url, path = await upload_file_to_gcp(
    file=uploaded_file,
    entity_type="users",
    entity_id=user.id,
    subfolder="avatar"
)

# Save path to database
user.avatar_path = path
await session.flush()
```

#### With Custom Validation

```python
# Custom allowed types dan max size
signed_url, path = await upload_file_to_gcp(
    file=uploaded_file,
    entity_type="users",
    entity_id=user.id,
    subfolder="documents",
    allowed_types=settings.ALLOWED_DOCUMENT_TYPES,
    max_size=settings.MAX_DOCUMENT_SIZE
)
```

### Generate Signed URL

```python
from app.core.utils.file_upload import generate_signed_url_for_path

# Single file
url = generate_signed_url_for_path("users/123/avatar/abc.jpg")
# Result: "https://storage.googleapis.com/bucket/...?X-Goog-Signature=..."

# Multiple files
urls = generate_signed_urls_for_paths([
    "users/123/doc1.pdf",
    "users/123/doc2.pdf"
])
```

### Delete File

```python
from app.core.utils.gcp_storage import get_gcp_storage_client

storage_client = get_gcp_storage_client()

# Delete by path
success = storage_client.delete_file("users/123/avatar/old.jpg")

# Delete by URL
from app.core.utils.file_upload import delete_file_from_gcp_url
success = delete_file_from_gcp_url("https://storage.googleapis.com/...")
```

### Best Practices

**DO**:
✅ Always store **path** in database, not URL
✅ Generate signed URL on-demand saat response
✅ Delete old file sebelum upload new file
✅ Use `upload_file_to_gcp()` untuk auto-validation
✅ Handle upload errors gracefully (log warning, continue operation)

**DON'T**:
❌ Jangan store signed URL di database (expired dalam 7 hari)
❌ Jangan generate URL jika tidak perlu (waste resources)
❌ Jangan lupa delete old file saat update
❌ Jangan skip file validation

### Example: Add File Upload to New Entity

```python
# 1. Model - tambah field
class Farmer(Base):
    photo_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

# 2. Response schema - computed field
class FarmerResponse(BaseModel):
    photo_path: Optional[str] = Field(None, exclude=True)

    @computed_field
    @property
    def photo_url(self) -> Optional[str]:
        return generate_signed_url_for_path(self.photo_path)

# 3. Router - multipart endpoint
@router.patch("/{farmer_id}")
async def update_farmer(
    farmer_id: str,
    name: Optional[str] = Form(None),
    photo: Optional[UploadFile] = File(None),
    ...
):
    farmer = await service.update_farmer(farmer_id, data, photo_file=photo)

# 4. Service - handle upload
async def update_farmer(self, farmer_id: str, data, photo_file=None):
    farmer = await self.queries.get_by_id(farmer_id)

    if photo_file and photo_file.filename:
        signed_url, path = await upload_file_to_gcp(
            file=photo_file,
            entity_type="farmers",
            entity_id=farmer_id,
            subfolder="profile"
        )

        # Delete old
        if farmer.photo_path:
            storage_client = get_gcp_storage_client()
            storage_client.delete_file(farmer.photo_path)

        farmer.photo_path = path

    # Update other fields
    ...
```

### Security Notes

- **Private Bucket**: Bucket harus private, akses via signed URLs only
- **Signed URL Expiry**: Default 7 hari (configurable)
- **File Validation**: Always validate type & size sebelum upload
- **Path Storage**: Store path di DB, bukan URL (URL expires)
- **Access Control**: Only authenticated users bisa upload
- **Old File Cleanup**: Always delete old file saat update

---
