import operator

import pytest

from whodatbot.utils import extract_users


CASES = (
    # 1
    (
        {},
        [],
    ),
    # 2
    (
        {
            'message_id': 2,
            'date': 1573660000,
            'text': '/start',
            'from': {'is_bot': False, 'first_name': 'John', 'id': 123},
            'chat': {'type': 'private', 'first_name': 'John', 'id': 123},
            'entities': [{'type': 'bot_command', 'length': 5, 'offset': 0}],
        },
        [
            {
                'id': 123,
                'first_name': 'John',
                'last_name': None,
                'username': None,
            },
        ],
    ),
    # 3
    (
        {
            'message_id': 3,
            'date': 1573660000,
            'text': '/start',
            'from': {
                'is_bot': False, 'first_name': 'John',
                'last_name': 'Smith', 'id': 123,
            },
            'chat': {'type': 'supergroup', 'title': 'group name', 'id': -456},
        },
        [
            {
                'id': 123,
                'first_name': 'John',
                'last_name': 'Smith',
                'username': None,
            },
        ],
    ),
    # 4
    (
        {
            'message_id': 4,
            'forward_date': 1573660000,
            'date': 1573660005,
            'from': {'is_bot': False, 'first_name': 'John', 'id': 123},
            'chat': {'type': 'private', 'first_name': 'John', 'id': 123},
            'forward_from': {
                'is_bot': False, 'username': 'pak01',
                'first_name': 'Peter', 'id': 45,
            },
            'text': 'test',
        },
        [
            {
                'id': 123,
                'first_name': 'John',
                'last_name': None,
                'username': None,
            },
            {
                'id': 45,
                'first_name': 'Peter',
                'last_name': None,
                'username': 'pak01',
            },
        ],

    ),
    # 5
    (
        {
            'message_id': 5,
            'forward_date': 1573660000,
            'date': 1573660005,
            'from': {'is_bot': False, 'first_name': 'John', 'id': 123},
            'chat': {'type': 'private', 'first_name': 'John', 'id': 123},
            'forward_from': {
                'is_bot': True, 'username': 'tinystash_bot',
                'first_name': 'tiny[stash]', 'id': 419864769,
            },
            'text': 'test',
        },
        [
            {
                'id': 123,
                'first_name': 'John',
                'last_name': None,
                'username': None,
            },
        ],
    ),
    # 6
    (
        {
            'message_id': 6,
            'date': 1573660005,
            'from': {'is_bot': False, 'first_name': 'John', 'id': 123},
            'chat': {'type': 'supergroup', 'title': 'group name', 'id': -456},
            'reply_to_message': {
                'message_id': 3,
                'date': 1573660000,
                'from': {
                    'is_bot': False, 'username': 'pak01',
                    'first_name': 'Peter', 'id': 45,
                },
                'chat': {
                    'type': 'supergroup', 'title': 'group name', 'id': -456,
                },
                'text': 'ping',
            },
            'text': 'pong',
        },
        [
            {
                'id': 123,
                'first_name': 'John',
                'last_name': None,
                'username': None,
            },
            {
                'id': 45,
                'first_name': 'Peter',
                'last_name': None,
                'username': 'pak01',
            },
        ],
    ),
    # 7
    (
        {
            'message_id': 7,
            'date': 1573660005,
            'from': {'is_bot': False, 'first_name': 'John', 'id': 123},
            'chat': {'type': 'supergroup', 'title': 'group name', 'id': -456},
            'left_chat_member': {
                'is_bot': False, 'username': 'pak01',
                'first_name': 'Peter', 'id': 45,
            },
            'left_chat_participant': {
                'is_bot': False, 'username': 'pak01',
                'first_name': 'Peter', 'id': 45,
            },
        },
        [
            {
                'id': 123,
                'first_name': 'John',
                'last_name': None,
                'username': None,
            },
            {
                'id': 45,
                'first_name': 'Peter',
                'last_name': None,
                'username': 'pak01',
            },
        ],
    ),
    # 8
    (
        {
            'message_id': 8,
            'date': 1573660005,
            'from': {'is_bot': False, 'first_name': 'John', 'id': 123},
            'chat': {'type': 'supergroup', 'title': 'group name', 'id': -456},
            'new_chat_member': {
                'is_bot': False, 'username': 'pak01',
                'first_name': 'Peter', 'id': 45
            },
            'new_chat_members': [
                {
                    'is_bot': False, 'username': 'asdf',
                    'first_name': 'Roger', 'last_name': 'Smith', 'id': 67,
                },
                {
                    'is_bot': False, 'username': 'pak01',
                    'first_name': 'Peter', 'id': 45,
                },
            ],
        },
        [
            {
                'id': 123,
                'first_name': 'John',
                'last_name': None,
                'username': None,
            },
            {
                'id': 45,
                'first_name': 'Peter',
                'last_name': None,
                'username': 'pak01',
            },
            {
                'id': 67,
                'first_name': 'Roger',
                'username': 'asdf',
                'last_name': 'Smith',
            },
        ],
    ),
)


@pytest.mark.parametrize('msg,expected', CASES, ids=range(1, len(CASES) + 1))
def test(msg, expected):
    sort_key = operator.itemgetter('id')
    extracted = extract_users(msg)
    assert isinstance(extracted, list)
    assert sorted(extracted, key=sort_key) == sorted(expected, key=sort_key)
