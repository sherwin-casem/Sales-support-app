from src.common.enums import UserRole

ROLE_LEVEL: dict[UserRole, int] = {
    UserRole.SALES: 1,
    UserRole.MANAGER: 2,
    UserRole.ADMIN: 3,
}


def has_minimum_role(user_role: UserRole, minimum_role: UserRole) -> bool:
    return ROLE_LEVEL[user_role] >= ROLE_LEVEL[minimum_role]


def has_any_role(user_role: UserRole, allowed_roles: set[UserRole]) -> bool:
    return user_role in allowed_roles
