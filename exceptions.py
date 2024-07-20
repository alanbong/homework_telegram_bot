class APIResponseError(Exception):
    """Вызывается при некорректном ответе API."""

    pass


class HomeworkStatusError(Exception):
    """Вызывается при некорректром статусе домашней работы."""

    pass


class MissingTokensError(Exception):
    """Вызывается при отсутствующих переменных окружения."""

    pass
