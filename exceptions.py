class AbsenceVariables(Exception):
    """Ошибка переменных среды."""

    pass


class MainRequest(Exception):
    """Ошибка при запросе к основному API."""

    pass


class DecodingFailed(Exception):
    """Ошибка при расшифровки из формата JSON в тип данных Python."""

    pass


class TypeErrorDict(TypeError):
    """Данные не соответствуют типу в виде словаря."""

    pass


class TypeErrorList(TypeError):
    """Данные не соответствуют типу в виде списка."""

    pass


class MissingDataDict(Exception):
    """Отсутствие данных в словаре."""

    pass


class HomeworkKey(KeyError):
    """Данные не соответствуют типу в виде словаря."""

    pass


class HomeworkStatus(KeyError):
    """Отсутствует статус домашней работы."""

    pass


class HttpError(Exception):
    """Сбой в работе программы: Эндпоинт API-сервиса недоступен."""

    pass


class TelegramError(Exception):
    """Сбой в работе программы при отправке сообщения."""

    pass
