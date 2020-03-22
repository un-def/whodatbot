import logging
import string
from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar

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


class TemplateFormatter(string.Formatter):

    required_fields: Tuple[str, ...] = ()
    optional_fields: Tuple[str, ...] = ()

    def __init__(self, template: str) -> None:
        self._template = template
        self._check()

    def __call__(self, **kwargs: Any) -> str:
        return self.format(self._template, **kwargs)

    def _check(self) -> None:
        actual_fields = set()
        for _, field, format_spec, conversion in self.parse(self._template):
            if not field:
                continue
            if format_spec:
                raise ValueError(f'format_spec is forbidden: {field}')
            if conversion:
                raise ValueError(f'conversion is forbidden: {field}')
            if field in self.required_fields:
                actual_fields.add(field)
            elif field in self.optional_fields:
                pass
            else:
                raise ValueError(f'unexpected field: {field}')
        missing_fields = set(self.required_fields) - actual_fields
        if missing_fields:
            missing = ', '.join(sorted(missing_fields))
            raise ValueError(f'missing field(s): {missing}')

    def get_value(self, key, args, kwargs):   # type: ignore
        assert not isinstance(key, int), 'unexpected positional formatting'
        if key in kwargs:
            return kwargs[key]
        return f'{{{key}}}'


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
