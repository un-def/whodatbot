import logging
from typing import Any, Dict, List, Optional, Type, TypeVar

from .types import Message, User, UserID


T = TypeVar('T')


class LoggerDescriptor:

    def __get__(self, instance: T, owner: Type[T]) -> logging.Logger:
        name = f'{owner.__module__}.{owner.__qualname__}'
        if instance is None:
            obj = owner
        else:
            obj = instance
        logger: Optional[logging.Logger]
        logger = getattr(obj, self._logger_attr_name, None)
        if logger is not None:
            return logger
        logger = logging.getLogger(name)
        setattr(obj, self._logger_attr_name, logger)
        return logger

    def __set_name__(self, owner: Type[T], name: str) -> None:
        self._logger_attr_name = f'__{name}'


def _extract_users(dct: Dict[str, Any], accum: Dict[UserID, User]) -> None:
    if 'id' in dct and 'first_name' in dct:
        user_id = dct['id']
        if not dct.get('is_bot', False) and user_id not in accum:
            accum[user_id] = {
                'id': user_id,
                'first_name': dct['first_name'],
                'last_name': dct.get('last_name'),
                'username': dct.get('username'),
            }
            return
    for value in dct.values():
        if isinstance(value, dict):
            _extract_users(value, accum)
        elif isinstance(value, list):
            for nested_value in value:
                if isinstance(nested_value, dict):
                    _extract_users(nested_value, accum)


def extract_users(msg: Message) -> List[User]:
    accum: Dict[UserID, User] = {}
    _extract_users(msg, accum)
    return list(accum.values())
