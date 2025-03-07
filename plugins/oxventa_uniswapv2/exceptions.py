class AlreadyTokenPair(Exception):
    def __init__(self, *args, pair_address: str):
        super().__init__(*args)

        self._pair_address = pair_address

    @property
    def pair_address(self):
        return self._pair_address