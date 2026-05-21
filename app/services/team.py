from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ForbiddenException, NotFoundException, ConflictException
from app.models import User, Team
from app.models.user import Role
from app.shemas.team import TeamCreate, TeamUpdate
from app.repositories import TeamRepository


class TeamService:
    def __init__(self, team_repository: TeamRepository) -> None:
        self.team_repository = team_repository

    async def get_all(self, current_user: User) -> list[Team]:
        if current_user.role == Role.manager:
            return await self.team_repository.get_all_by_manager_id(current_user.id)

        return await self.team_repository.get_all()

    async def get_by_id(self, id: int, current_user: User) -> Team:
        db_team = self.team_repository.get_by_id(id)

        if db_team is None:
            raise NotFoundException(f"Комманда с id {id} не найдена или неактивна")

        if current_user.role == Role.manager and db_team.manager_id != current_user.id:
            raise ForbiddenException(
                f"Команда не принадлежит руководителю с id {current_user.id}"
            )

        return db_team

    async def get_by_user(self, current_user: User) -> Team:
        return await self.get_by_id(current_user.id)

    async def create(self, team: TeamCreate, current_user: User) -> Team:
        if current_user.role == Role.manager and team.manager_id != current_user.id:
            raise ForbiddenException(
                "Руководитель может создавать команды только для себя"
            )

        try:
            return await self.team_repository.create(**team.model_dump())
        except IntegrityError:
            raise ConflictException("Команда с именем {team.name} уже существует")

    async def update(self, id: int, team: TeamUpdate, current_user: User) -> Team:
        if current_user.role == Role.manager and team.manager_id != current_user.id:
            raise ForbiddenException("Руководитель может обновлять только свои команды")

        db_team = await self.get_by_id(id, current_user)

        try:
            return await self.team_repository.update(db_team, **team.model_dump())
        except IntegrityError:
            return ConflictException(f"Команда с именем {team.name} уже существует")

    async def deactivate(self, id: int, current_user: User) -> None:
        db_team = self.get_by_id(id, current_user)
        await self.team_repository.deactivate(db_team)

    # Неправильно, переделать. get_by_id() возвращает активные объекты
    async def activate(self, id: int, current_user: User) -> None:
        db_team = self.get_by_id(id, current_user)
        await self.team_repository.activate(db_team)
