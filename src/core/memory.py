class MemoryManager:
    def __init__(self):
        self.runtime = None
        self.table_name: str = None

    def get_memories(
        self,
        room_id: str,
        start: int,
        end: int,
        count: int = 10,
        unique: bool = True
    ):
        self.runtime