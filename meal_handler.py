import datetime
import logging

import requests, os
from misc import get_school_week
from bs4 import BeautifulSoup
from pprint import PrettyPrinter
import meal_prediction

logger = logging.getLogger(__name__)
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
			'sign_on':  requests.Request('POST', 'https://www.easistent.com/dijaki/ajax_prehrana_obroki_prijava', data=signing_on_data),
			'sign_off': requests.Request('POST', 'https://www.easistent.com/dijaki/ajax_prehrana_obroki_prijava', data=signing_off_data)
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

	def update_day(self, date: datetime.date):
		meals = self._get_meals(get_school_week(date))
		for date, options in meals.items():
			self._pick_meal(options[5])

	def _pick_meal(self, meal_option: dict):
			prepped = self.session.prepare_request(meal_option["actions"]["sign_on"])
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
		tables = soup.find_all('table', {'class':'ednevnik-seznam_ur_teden'})  # TODO compare with ither schools or find where entries are at
		meal_table = tables[1]  # only for sckr
		rows = meal_table.find_all('tr')
		meal_table.find('td', {'class': 'ednevnik-seznam_ur_teden-td ednevnik-seznam_ur_teden-ura', 'rowspan': True}).extract()  # removes 'Malica' with rowspan
		return_meals = {}
		for tr in rows[1:]:
			for td in tr.find_all('td'):
				meal_option = parse_meal_from_html(td)
				datum = meal_option["datum"]
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
	eas.meals.update_day(datetime.date(2019, 9, 30))
	print(eas.meals.predictor)
