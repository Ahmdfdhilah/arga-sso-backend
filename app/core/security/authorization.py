from typing import Callable, List, Optional, Union
from functools import wraps

from fastapi import Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.security import TokenService
from app.core.exceptions import UnauthorizedException, ForbiddenException
from app.core.enums import UserRole
from app.modules.auth.schemas import UserData


http_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
) -> UserData:
    if not credentials:
        raise UnauthorizedException("Token tidak ditemukan")

    try:
        payload = TokenService.verify_token(
            credentials.credentials, token_type="access"
        )

        user_id = payload.get("sub")

        user_role = payload.get("role")
        if user_role is None and user_id is None:
            raise UnauthorizedException("Data token tidak valid")
        return UserData(
            id=str(user_id),
            role=str(user_role),
            name=payload.get("name"),
            email=payload.get("email")
        )
    except Exception as e:
        raise UnauthorizedException(f"Token tidak valid: {str(e)}")


def require_role(*allowed_roles: Union[str, UserRole]):
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user: Optional[UserData] = kwargs.get("current_user")

            if not current_user:
                for arg in args:
                    if isinstance(arg, UserData):
                        current_user = arg
                        break

            if not current_user:
                raise UnauthorizedException("Autentikasi diperlukan")

            # Convert roles to string values for comparison
            role_values = [
                r.value if isinstance(r, UserRole) else r for r in allowed_roles
            ]

            if current_user.role not in role_values:
                raise ForbiddenException(
                    f"Akses ditolak. Role yang dibutuhkan: {', '.join(role_values)}"
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


class RoleChecker:
    def __init__(self, allowed_roles: List[Union[str, UserRole]]):
        # Convert all roles to string values for comparison
        self.allowed_roles = [
            r.value if isinstance(r, UserRole) else r for r in allowed_roles
        ]

    def __call__(self, current_user: UserData = Depends(get_current_user)) -> UserData:
        if current_user.role not in self.allowed_roles:
            raise ForbiddenException(
                f"Akses ditolak. Role yang dibutuhkan: {', '.join(self.allowed_roles)}"
            )
        return current_user


require_superadmin = RoleChecker([UserRole.SUPERADMIN])
require_admin = RoleChecker([UserRole.SUPERADMIN, UserRole.ADMIN])
require_user = RoleChecker([UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.USER])
require_any = RoleChecker(
    [UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.USER, UserRole.GUEST]
)
