from uuid import UUID
from src.core.logger import console
from src.core.types import MongoAdapterAbstract
from src.core.types import BrokerAdapterAbstract
from src.core.types import BrokerMessage
from src.core.exceptions import InvalidID

class BrokerAdapter(BrokerAdapterAbstract):
    def __init__(self, db: MongoAdapterAbstract):
        self.db = db

    def create_message(self, message_data: BrokerMessage):
        self.db.ensure_connection()
        try:
            self.db.database.get_collection("brokers").insert_one(
                message_data.model_dump()
            )
            return True
        except Exception as e:
            console.error(f"Error creating a message: {e}")
            return False
        
    def get_message(self, publisher: str):
        self.db.ensure_connection()

        message = self.db.database.get_collection("brokers").find_one({
            "publisher": publisher
        })
        if message:
            # self.remove_message_by_publisher(message["publisher"])
            return BrokerMessage(**message)
        return None
    
    def remove_message(self, uuid: UUID):
        self.db.ensure_connection()

        if isinstance(uuid, str):
            try:
                uuid = UUID(uuid)
            except ValueError:
                raise InvalidID("Invalid uuid")
        
        try:
            self.db.database.get_collection("brokers").delete_one({
                "uuid": uuid
            })
            return True
        except Exception as e:
            console.error(f"Error removing a message with uuid {uuid}: {e}")
            return None
    
    def remove_message_by_publisher(self, publisher: str):
        try:
            self.db.database.get_collection("brokers").delete_one({
                "publisher": publisher
            })
            return True
        except Exception as e:
            console.error(f"Error removing a message with publisher {publisher}: {e}")
            return None