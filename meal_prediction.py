from abc import ABC, abstractmethod
import shelve
import logging
logger = logging.getLogger(__name__)


class MealPredictor(ABC):
	def __init__(self):
		super().__init__()

	@abstractmethod
	def select_meal(self, e: list) -> dict:
		pass


class MealPredictorFromDB(MealPredictor):
	def __init__(self, db_path: str):
		super(MealPredictorFromDB, self).__init__()
		self.db_path = db_path
		self.db = self.get_db()
		logger.debug("Starting on db: " + str(self.db))

	def select_meal(self, e: list) -> dict:
		pass

	def train(self):
		pass

	def manual_select(self, e: list):
		pass

	def populate(self, data: list):
		with shelve.open(self.db_path, writeback=True) as shelve_db:
			shelve_db["items"] += data
			shelve_db.sync()

	def get_db(self):
		ret_obj = {}
		with shelve.open(self.db_path, writeback=True) as shelve_db:
			for k in shelve_db:
				ret_obj[k] = shelve_db[k]
		return ret_obj
