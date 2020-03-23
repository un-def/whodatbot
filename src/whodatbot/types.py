from typing import Any, Dict, NewType, Optional, TypedDict


UpdateID = NewType('UpdateID', int)

Update = Dict[str, Any]
Message = Dict[str, Any]


UserID = NewType('UserID', int)


class User(TypedDict):
    id: UserID
    first_name: str
    last_name: Optional[str]
    username: Optional[str]
