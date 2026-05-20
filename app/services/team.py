from sqlalchemy.exc import MultipleResultsFound

from app.core.exceptions import NotFoundException, ConflictException
from app.models import Team, Employee
from app.repositories import TeamRepository


class TeamService:
    def __init__(self, team_repository: TeamRepository) -> None:
        self.team_repository = team_repository

    async def get_all_teams(self) -> list[Team]:
        return await self.team_repository.get_all_active()

    async def get_team_by_id(self, id: int) -> Team | None:
        team = await self.team_repository.get_by_id(id)
        # я убрал try-except, в нем нет смысла, тк если айди повторится,
        # ошибка и так выйдет, однако если сама бд наебнется, то мы не найдем баг ибо у нас все завернуто в трай эксепт

        if not team:
            raise NotFoundException(f"Команда с ID {id} не найдена или неактивна")

        return team

    async def get_members(self, id: int) -> list[Employee]:
        members = await self.team_repository.get_members_by_team_id(id)

        return list(members)