from abc import ABC, abstractmethod
import shelve


class MealPredictor(ABC):
	def __init__(self):
		super().__init__()

	@abstractmethod
	def select_meal(self, e: list) -> dict:
		pass


class MealPredictorFromDB(MealPredictor):
	def __init__(self, db_path: str):
		super(MealPredictorFromDB, self).__init__()
		self.db = {}
		self.db_path = db_path

	def select_meal(self, e: list) -> dict:
		pass

	def train(self):
		pass

	def populate(self, data: list):
		with shelve.open(self.db_path) as shelve_db:
			shelve_db["items"] += data
			self.db = shelve_db
			shelve_db.sync()
