from pymongo import ReturnDocument


class ListenRepository:
    def __init__(self, collection):
        self.collection = collection

    def insert_listen(self, document):
        self.collection.insert_one(document)
        return document

    def find_listen(self, identifier):
        return self.collection.find_one({"_id": identifier})

    def update_listen(self, identifier, changes):
        return self.collection.find_one_and_update(
            {"_id": identifier}, {"$set": changes}, return_document=ReturnDocument.AFTER
        )

    def replace_listen(self, identifier, document):
        return self.collection.find_one_and_replace(
            {"_id": identifier}, document, return_document=ReturnDocument.AFTER
        )

    def delete_listen(self, identifier):
        return self.collection.delete_one({"_id": identifier}).deleted_count == 1

    def find_listens(self, query, offset, limit, sort_by, direction):
        return self.collection.find(query).sort([(sort_by, direction), ("_id", direction)]).skip(offset).limit(limit)

    def count_listens(self, query):
        return self.collection.count_documents(query)

    def aggregate_listens(self, pipeline):
        return self.collection.aggregate(pipeline, allowDiskUse=True)
