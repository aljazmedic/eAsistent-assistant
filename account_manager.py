#!/usr/bin/python3
import base64
import logging
import os
import pickle
from getpass import getpass
import util
from Crypto.Cipher import AES
from typing import List, Union
from pbkdf2 import PBKDF2
import random, string
logger = logging.getLogger(__name__)


def generate_salt(size=16):
	return "".join([random.choice(string.ascii_lowercase + string.ascii_uppercase + string.ascii_letters) for _ in range(size)])


#TODO Typing
class AccountManager:
	def __init__(self, pseudorandom_db_name):
		util.load_dotenv()
		self.salt_seed = os.getenv("SA_ACCOUNT_MANAGER_SALT_SEED", None)
		if not self.salt_seed:
			self.salt_seed = generate_salt(16)
			util.write_to_dotenv("SA_ACCOUNT_MANAGER_SALT_SEED", self.salt_seed)

		self.PASS_PHRASE_ENV_NAME = "SA_ACCOUNT_MANAGER_KEY"
		self.SECRETS_DB_FILE = './private/' + pseudorandom_db_name
		self.PASS_PHRASE_SIZE = 64  # 512-bit passphrase
		self.KEY_SIZE = 32  # 256-bit key
		self.BLOCK_SIZE = 16  # 16-bit blocks
		self.IV_SIZE = 16  # 128-bits to initialise
		self.SALT_SIZE = 8  # 64-bits of salt

		self.pass_phrase = ""

		# Setup
		try:
			logger.debug(f"Reading {self.PASS_PHRASE_ENV_NAME}")
			util.load_dotenv()
			self.pass_phrase = bytes(os.getenv(self.PASS_PHRASE_ENV_NAME, ""), encoding="ASCII")

			if len(self.pass_phrase) == 0:
				raise IOError
		except IOError as ioe:
			logger.debug("Generating passphrase")
			self.pass_phrase = os.urandom(self.PASS_PHRASE_SIZE)  # Random passphrase
			util.write_to_dotenv(self.PASS_PHRASE_ENV_NAME, str(base64.b64encode(self.pass_phrase), encoding="UTF-8"))
			try:
				os.remove(self.SECRETS_DB_FILE)  # If the passphrase has to be regenerated, then the old secrets file is irretrievable and should be removed
			except FileNotFoundError:
				pass
			logger.debug("Passphrase generated")
		else:
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
		return PBKDF2(db_key, self.salt_seed).read(self.SALT_SIZE)  # Salt is generated as the hash of the key with it's own salt acting like a seed value

	def _encrypt(self, plaintext: bytes, salt):
		logger.debug("Encrypting")
		''' Pad plaintext, then encrypt it with a new, randomly initialised cipher. Will not preserve trailing whitespace in plaintext!'''

		# Initialise Cipher Randomly
		initVector = os.urandom(self.IV_SIZE)

		# Prepare cipher key:
		cypher_key = PBKDF2(self.pass_phrase, salt).read(self.KEY_SIZE)

		cipher = AES.new(cypher_key, AES.MODE_CBC, initVector)  # Create cipher

		return initVector + cipher.encrypt(plaintext + b' '*(self.BLOCK_SIZE - (len(plaintext) % self.BLOCK_SIZE)))  # Pad and encrypt

	def _decrypt(self, cipher_text: bytes, salt):
		logger.debug("Decrypting")
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
	def store(self, db_key: str, value: str):
		''' Sore key-value pair safely and save to disk.'''
		self.db[db_key] = self._encrypt(bytes(value, encoding="UTF-8"), self._get_salt_for_key(db_key))
		self._write_db()

	def remove(self, db_key: str, *keys: str):
		if not keys:
			keys = [db_key]
		else:
			keys = [db_key] + list(keys)
		for k in keys:
			del self.db[k]
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
		''' Test if key is stored, if not, prompt the user for it while hiding their input from shoulder-surfers.'''
		if db_key not in self.db:
			val = getpass(prompt=f'{db_key.title()}:')
			if isinstance(val, str):
				s_val = val
			elif isinstance(val, bytes):
				s_val = str(val, encoding="UTF-8")
			else:
				raise ValueError
			self.store(db_key, s_val)

	def has_key(self, db_key: str):
		return db_key in self.db

	def get_keys(self):
		return self.db.keys()


if __name__ == '__main__':
	logging.basicConfig(level=logging.INFO)
	### Setup ###
	# Aquire passphrase:
	logger.debug("Aquiring passphrase")
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