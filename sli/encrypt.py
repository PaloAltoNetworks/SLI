import base64
import hashlib
from Crypto import Random
from Crypto.Cipher import AES
import json

"""
Class to provide encryption and decryption capabilities to various strings throughout project
credit to: https://stackoverflow.com/questions/12524994/encrypt-decrypt-using-pycrypto-aes-256
Modified to accept strings and dictionaries.
"""


class Encryptor(object):

    def __init__(self, key):
        self.bs = AES.block_size
        self.key = hashlib.sha256(key.encode()).digest()

    def encrypt(self, raw):
        """
        Encrypt string raw

        :param raw: string to encrypt
        :type raw: str

        :return: base64 encoded encrypted string
        :rtype: str
        """
        raw = self._pad(raw)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(raw.encode())).decode('utf-8')

    def decrypt(self, enc):
        """
        Encrypt encrypted string

        :param enc: string of encrypted text to decrypt
        :type enc: str

        :return: decrypted contents of enc string
        :rtype: str
        """
        enc = base64.b64decode(enc.encode())
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self._unpad(cipher.decrypt(enc[AES.block_size:])).decode('utf-8')

    def encrypt_dict(self, obj):
        """
        Encrypt a dictionary, returning encrypted string encoded in Base64

        :param obj: dictionary object to tbe encrypted
        :type obj: dict

        :return: encrypted string representing obj
        :rtype: str
        """
        return self.encrypt(json.dumps(obj))

    def decrypt_dict(self, enc):
        """
        Decrypt and return a dictionary stored in encrypted string enc

        :param enc: string of encrypted text to decrypt
        :type enc: str

        :return: dict of contents stored in enc
        :rtype: dict
        """
        return json.loads(self.decrypt(enc))

    def _pad(self, s):
        return s + (self.bs - len(s) % self.bs) * chr(self.bs - len(s) % self.bs)

    @staticmethod
    def _unpad(s):
        return s[:-ord(s[len(s)-1:])]
