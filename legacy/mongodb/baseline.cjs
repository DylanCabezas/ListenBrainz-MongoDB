const collection = db.getSiblingDB('listenbrainz_db').listens;
printjson({count: collection.countDocuments({}), sample: collection.findOne({}, {_id: 1})});
