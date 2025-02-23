import binascii
from src.crypto.aes import AESCipher

secret = b"b665a7839a585853e2cf961a689c81c7d5242ad8917313cd09baef216dfc4b9c"
aes = AESCipher(binascii.unhexlify(secret))
a = aes.encrypt("Hello World")
print (a)