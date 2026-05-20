from fastapi import HTTPException, status


class AppException(HTTPException):
    pass


class BadRequestException(AppException):
    def __init__(self, detail="Некорректный запросж."):
        super().__init__(status.HTTP_400_BAD_REQUEST, detail)


class UnauthorizedException(AppException):
    def __init__(self, detail: str = "Не удалось проверить учетные данные") -> None:
        super().__init__(
            status.HTTP_401_UNAUTHORIZED, detail, {"WWW-Authenticate": "Bearer"}
        )


class ForbiddenException(AppException):
    def __init__(self, detail="Доступ к ресурсу запрещен"):
        super().__init__(status.HTTP_403_FORBIDDEN, detail)


class NotFoundException(AppException):
    def __init__(self, detail: str = "Ресурс не найден") -> None:
        super().__init__(status.HTTP_404_NOT_FOUND, detail)


class ConflictException(AppException):
    def __init__(
        self, detail: str = "Текущее состояние ресурса конфликтует с запросом"
    ) -> None:
        super().__init__(status.HTTP_409_CONFLICT, detail)
