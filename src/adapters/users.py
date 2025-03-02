from uuid import UUID
from src.core.logger import console
from src.core.types import MongoAdapterAbstract
from src.core.types import Users
from src.core.types import UserAdapterAbstract
from src.core.exceptions import InvalidID

class UserAdapter(UserAdapterAbstract):
    def __init__(self, db: MongoAdapterAbstract):
        self.db: MongoAdapterAbstract = db

    def create_user(self, user_data: Users):
        self.db.ensure_connection()
        try:
            self.db.database.get_collection("users").insert_one(
                user_data.model_dump()
            )
            return True
        except Exception as e:
            console.error(f"Error creating a user: {e}")
            return False
        
    def get_user(self, user_id: UUID):
        self.db.ensure_connection()
        if isinstance(user_id, str):
            try:
                user_id = UUID(user_id)
            except ValueError:
                raise InvalidID("Invalid user id")
            
        user = self.db.database.get_collection("users").find_one({
            'uuid': user_id
        })
        if user:
            return Users(**user)
        return None
    
    def exists_user(self, user_id: UUID):
        user = self.get_user(user_id=user_id)
        if user is None: return False
        return True