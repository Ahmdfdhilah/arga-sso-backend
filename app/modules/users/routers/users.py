from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query, status, UploadFile, File, Form, Request

from app.core.schemas import (
    BaseResponse,
    DataResponse,
    PaginatedResponse,
    PaginationMeta,
)
from app.core.security import get_current_user, require_admin
from app.modules.auth.schemas import UserData
from app.modules.users.dependencies import UserServiceDep
from app.modules.users.schemas import (
    UserCreateRequest,
    UserUpdateRequest,
    UserResponse,
    UserListItemResponse,
)

router = APIRouter()


@router.get(
    "/me",
    response_model=DataResponse[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
)
async def get_my_profile(
    service: UserServiceDep,
    current_user: UserData = Depends(get_current_user),
) -> DataResponse[UserResponse]:
    user = await service.get(current_user.id)
    return DataResponse(
        error=False,
        message="Profil berhasil diambil",
        data=user,
    )


@router.patch(
    "/me",
    response_model=DataResponse[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="Update current user profile",
)
async def update_my_profile(
    service: UserServiceDep,
    current_user: UserData = Depends(get_current_user),
    name: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    avatar: Optional[UploadFile] = File(None, description="Avatar image (optional, max 5MB)"),
) -> DataResponse[UserResponse]:
    """
    Update profil user. Semua field optional.
    - Bisa update data saja tanpa avatar
    - Bisa update avatar saja tanpa data
    - Bisa update keduanya sekaligus
    - Avatar: JPG/PNG/WEBP, max 5MB

    PATCH semantics: only fields present in FormData will be updated.
    """

    update_data = UserUpdateRequest(
        **{k: v for k, v in {
            "name": name,
            "email": email,
            "phone": phone,
        }.items() if v is not None}
    )

    user = await service.update(current_user.id, update_data, avatar_file=avatar)
    return DataResponse(
        error=False,
        message="Profil berhasil diperbarui",
        data=user,
    )


@router.get(
    "/{user_id}",
    response_model=DataResponse[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="Get user by ID (Admin only)",
)
async def get_user(
    user_id: str,
    service: UserServiceDep,
    current_user: UserData = Depends(require_admin),
) -> DataResponse[UserResponse]:
    user = await service.get(user_id)
    return DataResponse(
        error=False,
        message="User berhasil diambil",
        data=user,
    )


@router.get(
    "",
    response_model=PaginatedResponse[UserListItemResponse],
    status_code=status.HTTP_200_OK,
    summary="List all users (Admin only)",
)
async def list_users(
    service: UserServiceDep,
    current_user: UserData = Depends(require_admin),
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=250)] = 20,
    status_filter: Optional[str] = Query(None, alias="status"),
    role: Optional[str] = None,
    search: Optional[str] = Query(None, description="Search by name or email"),
) -> PaginatedResponse[UserListItemResponse]:
    users, total = await service.list(
        page=page,
        limit=limit,
        status=status_filter,
        role=role,
        search=search,
    )

    total_pages = (total + limit - 1) // limit

    return PaginatedResponse(
        error=False,
        message=f"Ditemukan {total} users",
        data=users,
        meta=PaginationMeta(
            page=page,
            limit=limit,
            total_items=total,
            total_pages=total_pages,
            has_prev_page=page > 1,
            has_next_page=page < total_pages,
        ),
    )


@router.post(
    "",
    response_model=DataResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create user (Admin only)",
)
async def create_user(
    data: UserCreateRequest,
    service: UserServiceDep,
    current_user: UserData = Depends(require_admin),
) -> DataResponse[UserResponse]:
    user = await service.create(data)
    return DataResponse(
        error=False,
        message="User berhasil dibuat",
        data=user,
    )


@router.patch(
    "/{user_id}",
    response_model=DataResponse[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="Update user (Admin only)",
)
async def update_user(
    user_id: str,
    data: UserUpdateRequest,
    service: UserServiceDep,
    current_user: UserData = Depends(require_admin),
) -> DataResponse[UserResponse]:
    user = await service.update(user_id, data)
    return DataResponse(
        error=False,
        message="User berhasil diperbarui",
        data=user,
    )


@router.delete(
    "/{user_id}",
    response_model=BaseResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete user (Admin only)",
)
async def delete_user(
    user_id: str,
    service: UserServiceDep,
    current_user: UserData = Depends(require_admin),
) -> BaseResponse:
    await service.delete(user_id)
    return BaseResponse(
        error=False,
        message="User berhasil dihapus",
    )
