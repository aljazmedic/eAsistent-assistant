from abc import ABC, abstractmethod
import shelve
import logging, random

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
		return self.manual_select(e)

	def manual_select(self, list_of_options: list) -> dict:
		this_data = list_of_options[0]['datum']
		print(f"Options for {this_data}:")
		for i, meal_option in enumerate(list_of_options, start=1):
			print("{}.	{}\n	({})".format(i, meal_option["name"], meal_option["description"]))
		predicted = self._predict(list_of_options)
		# Choose, if typed, otherwise take prediction
		num_chosen = -1
		while num_chosen < 0 or num_chosen >= len(list_of_options):
			try:
				feed_back = input(f"Pick option for {this_data} ({predicted+1}):")
				if feed_back == "":
					num_chosen = predicted
				else:
					num_chosen = int(feed_back) - 1
			except ValueError:
				print("Invalid entry!")
				pass
			except Exception as e:
				raise e
		logger.info(f"Chosen number {num_chosen+1} ({list_of_options[num_chosen]['name']}) for date {this_data}.")
		return list_of_options[num_chosen]

	def _predict(self, list_of_options: list) -> int:
		with shelve.open(self.db_path, writeback=True) as shelve_db:
			pass
		return random.randint(0, len(list_of_options) - 1)

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
