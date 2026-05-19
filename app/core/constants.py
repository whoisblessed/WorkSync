from app.models.user import Role

ROLE_CREATION_PERMISSIONS = {
    Role.employee: [Role.employee],
    Role.hr: [Role.employee, Role.hr],
    Role.manager: [Role.employee, Role.hr, Role.manager],
}
