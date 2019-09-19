import datetime
import logging

from eassistant_connection import EAssistantService

logger = logging.getLogger(__name__)


class MealHandler:

	def __init__(self, easervice: EAssistantService):
		self.ea_service = easervice

	def update_day(self, date: datetime.date):
		pass


if __name__ == '__main__':
	pass
