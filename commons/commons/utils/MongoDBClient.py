from pymongo import MongoClient,errors
import logging
from commons.config import MONGO_URI, DB_name

logger = logging.getLogger(__name__)

class MongoDBClient:
    def __init__(self):
        _client = None
        _db = None

        @classmethod
        def init_connection(cls):
            if cls._client is None:
                try:
                    cls._client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
                    cls._client.admin.command('ping')
                    cls._db = cls._client[DB_name]
                    logger.info("✅ MongoDB connection established.")
                except errors.ConnectionError as e:
                    logger.error(f"❌ Failed to connect to MongoDB: {e}")
                    raise


        def get_collection(cls, name):
            if cls._db is None:
                cls.init_connection()
            return cls._db[name]