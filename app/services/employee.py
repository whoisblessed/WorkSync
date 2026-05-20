from sqlalchemy.exc import IntegrityError

from app.core.constants import ROLE_CREATION_PERMISSIONS
from app.core.exceptions import (
    ForbiddenException,
    NotFoundException,
    ConflictException,
)
from app.core.security import hash_password
from app.models import User
from app.shemas.user import UserCreate, UserUpdate
from app.repositories import EmployeeRepository


class EmployeeService:
    def __init__(self, employee_repository: EmployeeRepository) -> None:
        self.employee_repository = employee_repository
