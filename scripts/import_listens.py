import argparse
import sqlite3
import json
from pathlib import Path

from pymongo.errors import PyMongoError

from app.config import settings
from app.database import create_client
from app.services.import_service import import_file


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path)
    parser.add_argument('--state', type=Path, default=Path('data/import_state.sqlite3'))
    parser.add_argument('--limit', type=int, default=1000)
    parser.add_argument('--batch-size', type=int, default=1000)
    parser.add_argument('--target', type=int, default=4000000)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--full', action='store_true')
    args = parser.parse_args()
    if args.source is None:
        sources = list((Path(__file__).resolve().parents[1] / 'data').rglob('10.listens'))
        if len(sources) != 1:
            parser.error('Specify --source with one JSONL or .listens file')
        args.source = sources[0]
    if not 1 <= args.batch_size <= 5000 or not 1 <= args.target <= 4000000 or args.limit < 1:
        parser.error('Invalid limit, batch size or target')
    if args.full and not args.apply:
        parser.error('--full requires --apply')
    if args.limit > 10000 and not args.full:
        parser.error('More than 10000 lines requires --full --apply')
    return args


def main():
    args = parse_arguments()
    with create_client() as client:
        client.admin.command('ping')
        collection = client[settings.database_name][settings.collection_name]
        result = import_file(collection, args.source, args.state,
                             2**63 - 1 if args.full else args.limit,
                             args.batch_size, args.target, not args.apply, progress=True)
        print(json.dumps(result), flush=True)


if __name__ == '__main__':
    try:
        main()
    except (PyMongoError, OSError, ValueError, sqlite3.Error) as error:
        raise SystemExit(f'Import stopped; repeat after fixing the cause: {error}')
