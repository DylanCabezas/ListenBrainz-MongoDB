import sqlite3

from pymongo.errors import PyMongoError

from app.services.import_service import fingerprint, import_file, insert_batch, validate_document
from scripts.import_listens import main


if __name__ == '__main__':
    try:
        main()
    except (PyMongoError, OSError, ValueError, sqlite3.Error) as error:
        raise SystemExit(f'Import stopped; repeat after fixing the cause: {error}')
