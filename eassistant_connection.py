import logging, requests, json, base64
from bs4 import BeautifulSoup

def parse_user_data(path):
	with open(path) as rf:
		data = json.load(rf) 
	data["geslo"] = str(base64.b64decode(payload["geslo"].encode("utf-8")), "utf-8")
	return data

def init_session(s = None):
	logging.info("Initialization of session for eassistant.")
	if not s:
		s = requests.Session()
	#Initial get
	LOGIN_URL = "https://www.easistent.com/p/ajax_prijava"

	payload = parse_user_data("private/creds.json")

	post_request = s.post(LOGIN_URL, data=payload, allow_redirects=True)
	post_json = post_request.json()
	if post_request.status_code != 200 or len(post_json["errfields"]) != 0:
		raise Exception(post_request, post_request.text)
	print(post_json)
	rdrect = post_json["data"]["prijava_redirect"]

	get_request = s.get(rdrect)
	#get_request.encoding = 'ISO-8859-1'

	#Extract auth metas from html
	soup = BeautifulSoup(get_request.text, 'html.parser')
	metas = {}
	soup = soup.find("head").find_all("meta")

	for nm in soup:
		if nm.get("name", None) in ("x-child-id", "access-token", "refresh-token"):
			metas[nm.get("name", None)] = nm.get("content", "").strip()

	#update headers to achieve authorization level :OK  :)
	s.headers.update ({
			"Authorization":metas["access-token"],
			"X-Child-Id":metas["x-child-id"],
			"X-Client-Version": "13",
			"X-Client-Platform": "web",
			"X-Requested-With": "XMLHttpRequest"
		})
	logging.info("Session authenticated!")
	return s
