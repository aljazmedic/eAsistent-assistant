import datetime
import pickle
import logging
logger = logging.logger = logging.getLogger(__name__)

GOOGLE_EVENT_RANGE = 11


def hash_event(e):
	if e["type"] == "school_hour":
		N = 1
	elif e["type"] == "event":
		N = 2
	else:
		N = 3
	return f'id:{N}{(e.get("subject", e.get("name")).lower().replace("č", "c").replace("š", "s").replace("ž","z") + "___")[:3]}{extract_HHMM(e["start"]["dateTime"])}{extract_HHMM(e["end"]["dateTime"])}'


def str_to_colorId(input_str: str, range_n: int = GOOGLE_EVENT_RANGE, color_string=False) -> int:
	if color_string:
		return int(input_str[1]+input_str[3], 16)%range_n
	sum_of_ascii = 0
	for c in input_str:
		sum_of_ascii += ord(c)
	return int(sum_of_ascii * 101 + 37) % range_n + 1


class EventFormatter:
	def __init__(self):
		self.TIMEZONE = 'Europe/Belgrade'
		self.COLORMAP = self.load_colormap()

	def load_colormap(self) -> dict:
		r = {}
		try:
			with open("event_manager/COLORMAP.pickle", "rb") as CM_file:
				r = pickle.load(CM_file)
		except (FileNotFoundError, EOFError):
			with open("event_manager/COLORMAP.pickle", "wb") as CM_file:
				pickle.dump(r, CM_file)
		self.COLORMAP = r
		return r

	def write_colormap(self):
		with open("event_manager/COLORMAP.pickle", "wb") as CM_file:
			pickle.dump(self.COLORMAP, CM_file)

	def google_event_body_from_parsed_event(self, e: dict) -> (str, dict):
		specialty = e.get("special", None)
		if e["type"] == "school_hour":
			description = [
				f'Speciality: {e.get("special", "None")}',
				f'Classroom: {e["classroom"]}',
				f'Teachers: {", ".join(e["teachers"])}',
				f'#school {e["type"]} {e["hash"]}'
			]
			abbr_teachers = None
			if e["teachers"]:
				abbr_teachers = " ".join("".join([x[0].upper() for x in teacher.split(" ")]) for teacher in e["teachers"])
				addition = f'({":".join([e["classroom"][:3], abbr_teachers])})'
			summary = f'{e["subject"]}'
			if e.get("classroom", None) or abbr_teachers:
				summary += " " + addition
			BODY = {
				"summary": summary,
				"start": e["start"],
				"end": e["end"],
				"description": ("\n".join(description)).strip(),
				"colorId": self.COLORMAP[e["color"]]
			}
		elif e["type"] == "event":
			description = [
				f'Location: {e["location"]}',
				f'Teachers: {", ".join(e["teachers"])}',
				f'#school {e["type"]} {e["hash"]}'
			]
			abbr_teachers = None
			if e["teachers"]:
				abbr_teachers = " ".join("".join([x[0].upper() for x in teacher.split(" ")]) for teacher in e["teachers"])
				addition = f'({":".join([e.get("location", "")[:3], abbr_teachers])})'
			summary = f'{e["name"]}'
			if e.get("location", None) or abbr_teachers:
				summary += " " + addition
			BODY = {
				"summary": summary,
				"start": e["start"],
				"end": e["end"],
				"description": "\n".join(description),
				"colorId": str_to_colorId(str(hash(["start"]))+e["type"])
			}
		else:  # e["type"] == "all_day_event"
			description = [
				f'Location: {e["location"]}',
				f'Teachers: {", ".join(e["teachers"])}',
				f'Type: {e["event_type"]}',
				f'#school {e["type"]} {e["hash"]}'
			]
			abbr_teachers = None
			if e["teachers"]:
				abbr_teachers = " ".join("".join([x[0].upper() for x in teacher.split(" ")]) for teacher in e["teachers"])
				addition = f'({":".join([e.get("location", "")[:3], abbr_teachers])})'
			summary = f'{e["name"]}'
			if e.get("location", None) or abbr_teachers:
				summary += " " + addition
			BODY = {
				"summary": summary,
				"start": e["start"],
				"end": e["end"],
				"description": "\n".join(description),
				"colorId": str_to_colorId(str(hash(["start"]))+e["type"])
			}
		return specialty, BODY

	def format_timetable_for_entry(self, table):
		self.TIMEZONE = 'Europe/Belgrade'
		all_the_colors = set()

		def date_cmp(f, d1, d2, fmt="%Y-%m-%dT%H:%M:%S"):
			if d1 is None and d2:
				return d2
			elif d2 is None and d1:
				return d1
			elif d2 and d1:
				dt1 = datetime.datetime.strptime(d1, fmt)
				dt2 = datetime.datetime.strptime(d2, fmt)
				return f(dt1, dt2).isoformat()
			return None

		# instantiate translation dict (id -> data)
		translation_dict = {"time": {}, "date": {}}
		time_boundary = {"min": None, "max": None}
		for e in table["time_table"]:
			key = str(e["id"])
			translation_dict["time"][key] = {
				"name": e["name_short"],
				"time": {
					"from": datetime.datetime.strptime(e["time"]["from"], "%H:%M").time().isoformat(),
					"to": datetime.datetime.strptime(e["time"]["to"], "%H:%M").time().isoformat()
				}
			}

		for e in table["day_table"]:
			dtime = datetime.datetime.strptime(e["date"], "%Y-%m-%d").date()
			translation_dict["date"][dtime.isoformat()] = {
				"name": e["name"],
				"name_short": e["short_name"],
				"date": dtime.isoformat()
			}

		events = []
		for entry in table["school_hour_events"]:
			time_from_e = translation_dict["time"][str(entry["time"]["from_id"])]
			time_to_e = translation_dict["time"][str(entry["time"]["to_id"])]
			date_e = translation_dict["date"][str(entry["time"]["date"])]
			e = {
				"start": {'timeZone': self.TIMEZONE},
				"end": {'timeZone': self.TIMEZONE},
				"names": {
					"day_name": date_e["name"],
					"hour_name_from": time_from_e["name"],
					"hour_name_to": time_to_e["name"]
				},
				"type": "school_hour",
				"completed": entry["completed"],
				"subject": entry["subject"]["name"],
				"special": entry["hour_special_type"],
				"classroom": entry["classroom"]["name"],
				"teachers": [x["name"] for x in entry["teachers"]],
				"departments": [x["name"] for x in entry["departments"]],
				"groups": entry["groups"],
				"info": entry["info"],
				"color": entry["color"]
			}
			e["start"]["dateTime"] = date_e["date"] + 'T' + time_from_e["time"]["from"]
			e["end"]["dateTime"] = date_e["date"] + 'T' + time_to_e["time"]["to"]

			time_boundary["min"] = date_cmp(min, time_boundary["min"], e["start"]["dateTime"])
			time_boundary["max"] = date_cmp(max, time_boundary["max"], e["end"]["dateTime"])

			e["hash"] = hash_event(e)
			all_the_colors.add(e["color"])  # Add Color for color mapping to Google's 11 color combinations
			events.append(e)

		for entry in table["events"]:
			time_from = datetime.datetime.strptime(entry["time"]["from"], "%H:%M").time().isoformat()
			time_to = datetime.datetime.strptime(entry["time"]["to"], "%H:%M").time().isoformat()
			date_e = translation_dict["date"][str(entry["date"])]
			e = {
				"start": {'timeZone': self.TIMEZONE},
				"end": {'timeZone': self.TIMEZONE},
				"names": {
					"day_name": date_e["name"]
				},
				"time": {
					"day_name": date_e["name"]
				},
				"type": "event",
				"name": entry["name"],
				"location": entry["location"]["name"],
				"teachers": [x["name"] for x in entry["teachers"]]
			}

			e["start"]["dateTime"] = date_e["date"] + 'T' + time_from
			e["end"]["dateTime"] = date_e["date"] + 'T' + time_to

			time_boundary["min"] = date_cmp(min, time_boundary["min"], e["start"]["dateTime"])
			time_boundary["max"] = date_cmp(max, time_boundary["max"], e["end"]["dateTime"])

			e["hash"] = hash_event(e)
			events.append(e)

		for entry in table["all_day_events"]:
			date_e = translation_dict["date"][str(entry["date"])]
			e = {
				"start": {'timeZone': self.TIMEZONE},
				"end": {'timeZone': self.TIMEZONE},
				"names": {
					"day_name": date_e["name"]
				},
				"name": entry["name"],
				"type": "all_day_event",
				"event_type": entry["event_type"],
				"location": entry["location"]["name"],
				"teachers": [x["name"] for x in entry["teachers"]],
			}
			e["start"]["date"] = date_e["date"]
			e["end"]["date"] = date_e["date"]

			time_boundary["min"] = date_cmp(min, time_boundary["min"], e["start"]["date"] + "T00:00:00")
			time_boundary["max"] = date_cmp(max, time_boundary["max"], e["end"]["date"] + "T00:00:00")

			e["hash"] = hash_event(e)
			events.append(e)

		time_boundary['timeZone'] = self.TIMEZONE

		if not self.COLORMAP:
			# Translate all_the_colors to COLORMAP
			for i, c in enumerate(all_the_colors, start=1):
				self.COLORMAP[c] = i % GOOGLE_EVENT_RANGE + 1
			self.write_colormap()
		return {"translation": translation_dict, "time_boundary": time_boundary,
				"events": sorted(events, key=lambda x: x["start"].get("dateTime", x["start"].get("date")))}


""" HASH : [1|2|3]XXXSSSSEEEE
	1,2,3 event type
	XXX subj
	SSSS start HHMM
	EEEE end HHMM
"""


def extract_HHMM(iso_formatted_string):
	return iso_formatted_string[11:13] + iso_formatted_string[14:16]
