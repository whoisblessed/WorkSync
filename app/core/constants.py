from app.models.user import Role

ROLE_CREATION_PERMISSIONS = {
    Role.hr: [Role.employee, Role.hr],
    Role.manager: [Role.employee, Role.hr, Role.manager],
}
