import base64
import logging
import os
import pickle
from getpass import getpass

from Crypto.Cipher import AES
from pbkdf2 import PBKDF2


#TODO Typing
class AccountManager:
	def __init__(self):
		self.saltSeed = 'q34hregt346u57uz'  # MAKE THIS YOUR OWN RANDOM STRING

		self.PASS_PHRASE_FILE = './private/easistent_login.p'
		self.SECRETS_DB_FILE = './private/easistent_login'
		self.PASS_PHRASE_SIZE = 64  # 512-bit passphrase
		self.KEY_SIZE = 32  # 256-bit key
		self.BLOCK_SIZE = 16  # 16-bit blocks
		self.IV_SIZE = 16  # 128-bits to initialise
		self.SALT_SIZE = 8  # 64-bits of salt

		self.pass_phrase = ""

		# Setup
		try:
			logging.debug(f"Reading {self.PASS_PHRASE_FILE}")
			with open(self.PASS_PHRASE_FILE, 'rb') as f:
				self.pass_phrase = f.read()  # .encode('UTF-8')
				logging.debug(f" Loaded: {self.pass_phrase}")
			if len(self.pass_phrase) == 0:
				raise IOError
		except IOError:
			logging.debug("Generating passphrase")
			with open(self.PASS_PHRASE_FILE, 'wb') as f:
				self.pass_phrase = os.urandom(self.PASS_PHRASE_SIZE)  # Random passphrase
				f.write(base64.b64encode(self.pass_phrase))
				try:
					os.remove(self.SECRETS_DB_FILE)  # If the passphrase has to be regenerated, then the old secrets file is irretrievable and should be removed
				except FileNotFoundError:
					pass
			logging.debug("Passphrase generated")
		else:
			logging.debug(f"Decoding {self.pass_phrase}")
			self.pass_phrase = base64.b64decode(self.pass_phrase)  # Decode if loaded from already extant file

		# Load or create secrets database:
		try:
			with open(self.SECRETS_DB_FILE, 'rb') as f:
				self.db = pickle.load(f)
			if self.db == {}:
				raise IOError
		except (IOError, EOFError):
			self.db = {}  # start new db
			with open(self.SECRETS_DB_FILE, 'wb') as f:
				pickle.dump(self.db, f)

	def _get_salt_for_key(self, db_key):
		return PBKDF2(db_key, self.saltSeed).read(self.SALT_SIZE)  # Salt is generated as the hash of the key with it's own salt acting like a seed value

	def _encrypt(self, plaintext, salt):
		logging.debug("Encrypting")
		''' Pad plaintext, then encrypt it with a new, randomly initialised cipher. Will not preserve trailing whitespace in plaintext!'''

		# Initialise Cipher Randomly
		initVector = os.urandom(self.IV_SIZE)

		# Prepare cipher key:
		cypher_key = PBKDF2(self.pass_phrase, salt).read(self.KEY_SIZE)

		cipher = AES.new(cypher_key, AES.MODE_CBC, initVector)  # Create cipher

		return initVector + cipher.encrypt(plaintext + b' '*(self.BLOCK_SIZE - (len(plaintext) % self.BLOCK_SIZE)))  # Pad and encrypt

	def _decrypt(self, cipher_text, salt):
		logging.debug("Decrypting")
		''' Reconstruct the cipher object and decrypt. Will not preserve trailing whitespace in the retrieved value!'''

		# Prepare cipher key:
		key = PBKDF2(self.pass_phrase, salt).read(self.KEY_SIZE)

		# Extract IV:
		initVector = cipher_text[:self.IV_SIZE]
		cipher_text = cipher_text[self.IV_SIZE:]

		cipher = AES.new(key, AES.MODE_CBC, initVector)  # Reconstruct cipher (IV isn't needed for edecryption so is set to zeros)

		return cipher.decrypt(cipher_text).rstrip(b' ')  # Decrypt and depad

	def _write_db(self):
		with open(self.SECRETS_DB_FILE, 'wb') as f:
			pickle.dump(self.db, f)

	# ## User Functions ## #
	def store(self, db_key: str, value: bytes):
		''' Sore key-value pair safely and save to disk.'''
		self.db[db_key] = self._encrypt(value, self._get_salt_for_key(db_key))
		self._write_db()

	def remove(self, db_key: str):
		del self.db[db_key]
		self._write_db()

	def retrieve(self, db_key: str, request_if_none=False):
		''' Fetch key-value pair.'''
		if db_key in self.db:
			return str(self._decrypt(self.db.get(db_key), self._get_salt_for_key(db_key)), encoding='UTF-8')
		elif request_if_none:  # Prompts for it
			self.require(db_key)
			return self.retrieve(db_key)
		return None

	def require(self, db_key: str):
		logging.debug(f"Requiring {db_key}")
		''' Test if key is stored, if not, prompt the user for it while hiding their input from shoulder-surfers.'''
		if db_key not in self.db:
			self.store(db_key, getpass(prompt=f'{db_key.title()}:').encode('UTF-8'))

	def has_key(self, db_key: str):
		return db_key in self.db

	def get_keys(self):
		return self.db.keys()


if __name__ == '__main__':
	logging.basicConfig(level=logging.INFO)
	### Setup ###
	# Aquire passphrase:
	logging.debug("Aquiring passphrase")
	am = AccountManager()
	### Test (put your code here) ###
	am.require('id')
	am.require('password1')
	am.require('password2')
	print()
	print('Stored Data:')
	am.retrieve("tes")
	for key in am.get_keys():
		print(key, am.retrieve(key))  # decode values on demand to avoid exposing the whole database in memory
	# DO STUFF