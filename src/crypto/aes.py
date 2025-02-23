from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import base64

class AESCipher:
    def __init__(self, key: bytes) -> None:
        self.key = key

    def encrypt(self, raw: str) -> str:
        raw = self._pad(raw)
        iv = get_random_bytes(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        encrypted = cipher.encrypt(raw.encode('utf-8'))
        return base64.b64encode(iv + encrypted).decode('utf-8')

    def decrypt(self, enc: str) -> str:
        enc = base64.b64decode(enc)
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        decrypted = cipher.decrypt(enc[AES.block_size:])
        return self._unpad(decrypted).decode('utf-8')

    def _pad(self, s: str) -> str:
        pad_len = AES.block_size - len(s) % AES.block_size
        return s + (chr(pad_len) * pad_len)

    def _unpad(self, s: bytes) -> bytes:
        return s[:-ord(s[len(s)-1:])]

# Example usage:
# key = get_random_bytes(16)  # AES-128
# aes_cipher = AESCipher(key)
# encrypted = aes_cipher.encrypt('Hello World')
# decrypted = aes_cipher.decrypt(encrypted)
# print(f'Encrypted: {encrypted}')
# print(f'Decrypted: {decrypted}')