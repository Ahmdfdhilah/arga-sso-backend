from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status, Form, File, UploadFile

from app.core.schemas import (
    BaseResponse,
    DataResponse,
    PaginatedResponse,
    PaginationMeta,
)
from app.core.security import require_admin, get_current_user
from app.modules.auth.schemas import UserData
from app.modules.applications.dependencies import ApplicationServiceDep
from app.modules.applications.schemas import (
    ApplicationResponse,
    ApplicationListItemResponse,
    AllowedAppResponse,
    UserApplicationAssignRequest,
)

router = APIRouter()


@router.get(
    "",
    response_model=PaginatedResponse[ApplicationListItemResponse],
    status_code=status.HTTP_200_OK,
    summary="List all applications (Admin only)",
)
async def list_applications(
    service: ApplicationServiceDep,
    current_user: UserData = Depends(require_admin),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    is_active: bool | None = None,
) -> PaginatedResponse[ApplicationListItemResponse]:
    apps, total = await service.list(page=page, limit=limit, is_active=is_active)
    total_pages = (total + limit - 1) // limit

    return PaginatedResponse(
        error=False,
        message=f"Ditemukan {total} aplikasi",
        data=apps,
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
    response_model=DataResponse[ApplicationResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create application (Admin only)",
)
async def create_application(
    service: ApplicationServiceDep,
    name: str = Form(..., min_length=2, max_length=255),
    code: str = Form(..., min_length=2, max_length=100, pattern=r"^[a-z0-9_-]+$"),
    base_url: str = Form(..., min_length=1, max_length=500),
    description: Optional[str] = Form(None),
    single_session: bool = Form(False),
    img: Optional[UploadFile] = File(None),
    icon: Optional[UploadFile] = File(None),
   
    current_user: UserData = Depends(require_admin),
) -> DataResponse[ApplicationResponse]:
    app = await service.create(
        name=name,
        code=code,
        base_url=base_url,
        description=description,
        single_session=single_session,
        img_file=img,
        icon_file=icon,
    )
    return DataResponse(error=False, message="Aplikasi berhasil dibuat", data=app)


@router.get(
    "/my-apps",
    response_model=DataResponse[List[AllowedAppResponse]],
    status_code=status.HTTP_200_OK,
    summary="Get current user's applications",
)
async def get_my_applications(
    service: ApplicationServiceDep,
    current_user: UserData = Depends(get_current_user),
) -> DataResponse[List[AllowedAppResponse]]:
    apps = await service.get_user_applications(current_user.id)
    return DataResponse(
        error=False,
        message=f"User memiliki akses ke {len(apps)} aplikasi",
        data=apps,
    )


@router.get(
    "/{app_id}",
    response_model=DataResponse[ApplicationResponse],
    status_code=status.HTTP_200_OK,
    summary="Get application by ID (Admin only)",
)
async def get_application(
    app_id: str,
    service: ApplicationServiceDep,
    current_user: UserData = Depends(require_admin),
) -> DataResponse[ApplicationResponse]:
    app = await service.get(app_id)
    return DataResponse(error=False, message="Aplikasi berhasil diambil", data=app)


@router.patch(
    "/{app_id}",
    response_model=DataResponse[ApplicationResponse],
    status_code=status.HTTP_200_OK,
    summary="Update application (Admin only)",
)
async def update_application(
    app_id: str,
    service: ApplicationServiceDep,
    name: Optional[str] = Form(None, min_length=2, max_length=255),
    code: Optional[str] = Form(None, min_length=2, max_length=100, pattern=r"^[a-z0-9_-]+$"),
    base_url: Optional[str] = Form(None, min_length=1, max_length=500),
    description: Optional[str] = Form(None),
    is_active: Optional[bool] = Form(None),
    single_session: Optional[bool] = Form(None),
    img: Optional[UploadFile] = File(None),
    icon: Optional[UploadFile] = File(None),
    current_user: UserData = Depends(require_admin),
) -> DataResponse[ApplicationResponse]:
    app = await service.update(
        app_id=app_id,
        name=name,
        code=code,
        base_url=base_url,
        description=description,
        is_active=is_active,
        single_session=single_session,
        img_file=img,
        icon_file=icon,
    )
    return DataResponse(error=False, message="Aplikasi berhasil diperbarui", data=app)


@router.delete(
    "/{app_id}",
    response_model=BaseResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete application (Admin only)",
)
async def delete_application(
    app_id: str,
    service: ApplicationServiceDep,
    current_user: UserData = Depends(require_admin),
) -> BaseResponse:
    await service.delete(app_id)
    return BaseResponse(error=False, message="Aplikasi berhasil dihapus")


@router.get(
    "/user/{user_id}",
    response_model=DataResponse[List[AllowedAppResponse]],
    status_code=status.HTTP_200_OK,
    summary="Get user's applications (Admin only)",
)
async def get_user_applications(
    user_id: str,
    service: ApplicationServiceDep,
    current_user: UserData = Depends(require_admin),
) -> DataResponse[List[AllowedAppResponse]]:
    apps = await service.get_user_applications(user_id)
    return DataResponse(
        error=False,
        message=f"User memiliki akses ke {len(apps)} aplikasi",
        data=apps,
    )


@router.post(
    "/user/{user_id}/assign",
    response_model=DataResponse[List[AllowedAppResponse]],
    status_code=status.HTTP_200_OK,
    summary="Assign applications to user (Admin only)",
)
async def assign_applications_to_user(
    user_id: str,
    data: UserApplicationAssignRequest,
    service: ApplicationServiceDep,
    current_user: UserData = Depends(require_admin),
) -> DataResponse[List[AllowedAppResponse]]:
    apps = await service.assign_applications_to_user(user_id, data.application_ids)
    return DataResponse(
        error=False,
        message=f"Berhasil menetapkan {len(apps)} aplikasi ke user",
        data=apps,
    )


@router.delete(
    "/user/{user_id}/{app_id}",
    response_model=BaseResponse,
    status_code=status.HTTP_200_OK,
    summary="Remove application from user (Admin only)",
)
async def remove_application_from_user(
    user_id: str,
    app_id: str,
    service: ApplicationServiceDep,
    current_user: UserData = Depends(require_admin),
) -> BaseResponse:
    await service.remove_application_from_user(user_id, app_id)
    return BaseResponse(error=False, message="Aplikasi berhasil dihapus dari user")
