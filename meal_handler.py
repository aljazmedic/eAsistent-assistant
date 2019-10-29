import datetime
import logging

import requests
import os, threading
from util import get_school_week
from bs4 import BeautifulSoup
from pprint import PrettyPrinter
import meal_prediction
from google_calendar_connection import GoogleCalendarService
from time import sleep
from typing import Union, Dict, List
logger = logging.getLogger(__name__)
logging.getLogger("chardet").setLevel(logging.CRITICAL)
pp = PrettyPrinter(indent=4)


def parse_meal_from_html(e: BeautifulSoup) -> dict:
	divs = e.findChild('div').findChildren('div')
	if len(divs) != 3:
		# event already passed
		return {}
	click_event = divs[2].find('a')['onclick']  # read from onclick function
	click_event = click_event.split('(')[1].split(')')[0].split(', ')
	click_event = [c.replace('"', '').replace("'", '') for c in click_event]  # retrieve arguments for function
	fields = ['tip_prehrane', 'id_meni', 'datum', 'akcija', 'id_lokacija']
	signing_on_data = dict(zip(fields, click_event))  # merge them together
	signing_off_data = dict(zip(fields, click_event))
	signing_on_data["akcija"] = 'prijava'
	signing_off_data["akcija"] = 'odjava'

	r_object = {
		'name': ' '.join(divs[0].get_text().split()),
		'description': ' '.join(divs[1].get_text().split()),
		'actions': {
			'sign_on':  signing_on_data,
			'sign_off': signing_off_data
		},
		'datum': signing_on_data['datum'],
		'id_lokacija': signing_on_data['id_lokacija'],
		'id_meni': signing_on_data['id_meni'],
		'tip_prehrane': signing_on_data['tip_prehrane']
	}
	return r_object


class MealConnection:

	def __init__(self, easistent_session: requests.Session, predictor: callable, args: tuple):
		self.session = easistent_session
		self.predictor = predictor(*args)
		self.execution_requests = {}

	def _update_week(self, school_week: int):
		meals = self._get_meals(school_week)
		for date, options in meals.items():
			option = self.predictor.select_meal(options)
			self._pick_meal(option, execution_name=date)

	def create_execution_threads(self, logging_lock):
		# type: (threading.Lock) -> Dict
		ret_list_of_threads = {}

		# Function that a thread will run

		def do_function(dict_of_queues: dict, name: str, logging_lock_: threading.Lock):
			thread_name = f'eas_m_{name[5:]}'
			with logging_lock_:
				logger.info(f"Thread {thread_name} started with {len(dict_of_queues[name])} http requests.")

			while len(dict_of_queues[name]) >= 1:
				try:
					prepped, data = dict_of_queues[name].pop(0)
					response = self.session.send(prepped)

					response.encoding = 'ISO-8859-1'
					rsp_json = response.json()
					if rsp_json["status"].lower()[:2] != "ok" or response.status_code != 200:
						del rsp_json["data"]
						with logging_lock_:
							logging.exception(rsp_json)
						raise Exception(rsp_json["message"], *rsp_json["errfields"])
					sleep(1)
				except Exception as e:
					logger.debug(f"Error in executing queue: {thread_name}")
					logger.error(e)
			del dict_of_queues[name]
			with logging_lock_:
				logger.info(f"Thread {name} finished.")

		for name_of_queue, queue in self.execution_requests.items():
			ret_list_of_threads[name_of_queue] = threading.Thread(target=do_function,
																  args=(self.execution_requests, name_of_queue, logging_lock),
																  name=f'eas_m_{name_of_queue[5:]}')
		return ret_list_of_threads

	def update_meals(self, gcs: GoogleCalendarService, *dates: datetime.date):

		"""
		1.	Get meals for today
		2.	Pick meal
		3.	Get meal time prediction
		4.	Create event
		5.	Connect it to COLORMAP
		"""

		school_weeks = set()
		for d in dates:
			school_weeks.add(get_school_week(d))
		for week_num in school_weeks:
			self._update_week(week_num)

	def _pick_meal(self, meal_option: dict, execution_name=None):
			prepped = self.session.prepare_request(
				requests.Request('POST', 'https://www.easistent.com/dijaki/ajax_prehrana_obroki_prijava', data=meal_option["actions"]["sign_on"])
			)

			if execution_name:
				if execution_name not in self.execution_requests:
					self.execution_requests[execution_name] = [(prepped, meal_option)]
				else:
					self.execution_requests[execution_name].append((prepped, meal_option))

				logging.info("Queued pick meal: '" + meal_option["name"] + "' for day " + meal_option["datum"])
			else:
				response = self.session.send(prepped)
				response.encoding = 'ISO-8859-1'
				rsp_json = response.json()
				if rsp_json["status"].lower() == "ok":
					logging.info("Picked meal: '" + meal_option["name"] + "' for day " + meal_option["datum"])
				else:
					del rsp_json["data"]
					logging.exception(rsp_json)
					raise Exception(rsp_json["message"], *rsp_json["errfields"])

	def _get_meals(self, week_num: int):
		meal_url = 'https://www.easistent.com/dijaki/ajax_prehrana_obroki_seznam'
		data = {
			'qversion': '1',
			'teden': week_num,
			'smer': 'naprej'
		}
		response = self.session.post(meal_url, data=data, allow_redirects=True)
		response.encoding = 'ISO-8859-1'
		soup = BeautifulSoup(response.content, features="html.parser")
		tables = soup.find_all('table', {'class': 'ednevnik-seznam_ur_teden'})  # TODO compare with ither schools or find where entries are at
		meal_table = tables[1]  # only for sckr
		rows = meal_table.find_all('tr')
		meal_table.find('td', {'class': 'ednevnik-seznam_ur_teden-td ednevnik-seznam_ur_teden-ura', 'rowspan': True}).extract()  # removes 'Malica' with rowspan
		return_meals = {}
		for tr in rows[1:]:
			for td in tr.find_all('td'):
				meal_option = parse_meal_from_html(td)
				if not meal_option:
					continue
				datum = meal_option.get("datum")
				if datum in return_meals:
					return_meals[datum].append(meal_option)
				else:
					return_meals[datum] = [meal_option]
		return return_meals

	def _predict_from(self, options: list) -> dict:
		return self.predictor.select_meal(options)


if __name__ == '__main__':
	from eassistant_connection import EAssistantService
	logging.basicConfig(level=logging.DEBUG)
	logger.debug("Testing meal handler")
	eas = EAssistantService(meal_prediction.MealPredictorFromDB, tuple([os.path.join("temp", "db.db")]))
	eas.meals._update_day(datetime.date(2019, 9, 30))
	print(eas.meals.predictor)
