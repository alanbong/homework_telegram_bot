class APIResponseError(Exception):
    """Вызывается при некорректном ответе API."""

    pass


class HomeworkStatusError(Exception):
    """Вызывается при некорректром статусе домашней работы."""

    pass
