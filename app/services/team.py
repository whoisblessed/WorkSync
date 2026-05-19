from sqlalchemy.exc import MultipleResultsFound

from app.core.exceptions import NotFoundException, ConflictException
from app.models import Team
from app.repositories import TeamRepository


class TeamService:
    def __init__(self, team_repository: TeamRepository) -> None:
        self.team_repository = team_repository

    async def get_all_teams(self) -> list[Team]:
        return await self.team_repository.get_all_active()

    async def get_team_by_id(self, id: int) -> Team | None:
        try:
            team = await self.team_repository.get_active_by_id(id)
        except MultipleResultsFound:
            raise ConflictException(f"Найдено несколько команд с ID {id}")

        if team is None:
            raise NotFoundException(f"Команда с ID {id} не найдена или неактивна")

        return team
