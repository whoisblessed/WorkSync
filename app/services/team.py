from sqlalchemy.exc import IntegrityError

from app.core.constants import ROLE_CREATION_PERMISSIONS
from app.core.exceptions import ForbiddenException
from app.models import User, Team
from app.models.user import Role
from app.shemas.team import TeamCreate, TeamUpdate
from app.repositories import TeamRepository
from app.services import UserService



class TeamService:
    def __init__(self, team_repository: TeamRepository, user_service: UserService) -> None:
        self.team_repository = team_repository
        self.user_service = user_service
      
    async def get_all_by_manager_id(self, id: int, current_user: User) -> list[Team]:
        if current_user.role == Role.manager and id != current_user.id:
            raise ForbiddenException("Пользователям с ролью \"manager\" можно смотреть только свои команды")
        
        return await self.team_repository.get_all_by_manager_id(id)
    
    async def create(self, team: TeamCreate, current_user: User) -> Team:
        if current_user.role == Role.
        
        manager = await self.user_service.get_by_id(team.manager_id)
        