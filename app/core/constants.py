from app.models.user import Role

ROLE_CREATION_PERMISSIONS = {
    Role.hr: [Role.employee, Role.manager],
    Role.manager: [Role.employee],
}
