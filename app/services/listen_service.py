from bson import ObjectId

import base64
import binascii

from pydantic import ValidationError

from app.errors import InvalidListenError, ListenNotFoundError
from app.models import ListenCursor
from app.repositories.listen_repository import ListenRepository


def parse_identifier(value):
    if ObjectId.is_valid(value):
        return ObjectId(value)
    if value.startswith('listenbrainz:') and len(value) <= 200:
        return value
    raise InvalidListenError('Invalid listen identifier')


def serialize_listen(document):
    if document is None:
        raise ListenNotFoundError('Listen not found')
    return {**{key: value for key, value in document.items() if key != '_id'}, 'id': str(document['_id'])}


def build_filter(user_name=None, artist_name=None, start_timestamp=None, end_timestamp=None):
    if start_timestamp is not None and end_timestamp is not None and start_timestamp > end_timestamp:
        raise InvalidListenError('start_timestamp must not exceed end_timestamp')
    query = {}
    if user_name is not None:
        query['user_name'] = user_name
    if artist_name is not None:
        query['track_metadata.artist_name'] = artist_name
    bounds = {}
    if start_timestamp is not None:
        bounds['$gte'] = start_timestamp
    if end_timestamp is not None:
        bounds['$lte'] = end_timestamp
    if bounds:
        query['timestamp'] = bounds
    return query


def flatten_changes(values, prefix=''):
    changes = {}
    for key, value in values.items():
        path = f'{prefix}.{key}' if prefix else key
        if isinstance(value, dict) and value:
            changes.update(flatten_changes(value, path))
        else:
            changes[path] = value
    return changes


def encode_cursor(document):
    cursor = ListenCursor(timestamp=document['timestamp'], id=str(document['_id']),
                          id_type='objectId' if isinstance(document['_id'], ObjectId) else 'string')
    return base64.urlsafe_b64encode(cursor.model_dump_json().encode()).decode()


def decode_cursor(value):
    try:
        raw = base64.b64decode(value, altchars=b'-_', validate=True)
        cursor = ListenCursor.model_validate_json(raw)
        identifier = parse_identifier(cursor.id)
        if (cursor.id_type == 'objectId') != isinstance(identifier, ObjectId):
            raise ValueError('Identifier type mismatch')
        return cursor.timestamp, identifier
    except (ValueError, ValidationError, binascii.Error) as error:
        raise InvalidListenError('Invalid pagination cursor') from error


class ListenService:
    def __init__(self, collection):
        self.repository = ListenRepository(collection)

    def create_listen(self, payload):
        document = payload.model_dump(exclude_none=True)
        return serialize_listen(self.repository.insert_listen(document))

    def get_listen(self, listen_id):
        return serialize_listen(self.repository.find_listen(parse_identifier(listen_id)))

    def update_listen(self, listen_id, payload):
        changes = flatten_changes(payload.model_dump(exclude_unset=True))
        return serialize_listen(self.repository.update_listen(parse_identifier(listen_id), changes))

    def replace_listen(self, listen_id, payload):
        document = payload.model_dump(exclude_none=True)
        return serialize_listen(self.repository.replace_listen(parse_identifier(listen_id), document))

    def delete_listen(self, listen_id):
        if not self.repository.delete_listen(parse_identifier(listen_id)):
            raise ListenNotFoundError('Listen not found')

    def list_listens(self, query, page, limit, sort_by, sort_order):
        direction = 1 if sort_order == 'asc' else -1
        cursor = self.repository.find_listens(query, (page - 1) * limit, limit, sort_by, direction)
        return {'items': [serialize_listen(item) for item in cursor], 'page': page, 'limit': limit,
                'total': self.repository.count_listens(query)}

    def get_listen_feed(self, query, limit, cursor):
        if cursor:
            timestamp, identifier = decode_cursor(cursor)
            boundary = {'$or': [
                {'timestamp': {'$lt': timestamp}},
                {'timestamp': timestamp, '$expr': {'$lt': ['$_id', {'$literal': identifier}]}}
            ]}
            query = {'$and': [query, boundary]}
        documents = list(self.repository.find_listens(query, 0, limit + 1, 'timestamp', -1))
        items = documents[:limit]
        return {'items': [serialize_listen(document) for document in items],
                'next_cursor': encode_cursor(items[-1]) if len(documents) > limit else None}

    def get_summary(self, query):
        users = next(iter(self.repository.aggregate_listens([
            {'$match': query}, {'$group': {'_id': '$user_name'}}, {'$count': 'count'}
        ])), None)
        return {'total_listens': self.repository.count_listens(query),
                'unique_users': users['count'] if users else 0}

    def get_top_artists(self, query, limit):
        return list(self.repository.aggregate_listens([
            {'$match': query},
            {'$group': {'_id': '$track_metadata.artist_name', 'listen_count': {'$sum': 1}}},
            {'$sort': {'listen_count': -1, '_id': 1}}, {'$limit': limit},
            {'$project': {'_id': 0, 'artist_name': '$_id', 'listen_count': 1}},
        ]))
