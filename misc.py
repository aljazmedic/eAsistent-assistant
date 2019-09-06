import datetime
import json
import os
import requests
import shutil

import iso8601


def ask_for(session, method, url, counter=0, **kwargs):
	r = session.send(session.prepare_request(requests.Request(method, url, **kwargs)))
	r.encoding = 'ISO-8859-1'
	if r.status_code // 100 == 4 and counter < 2:
		print("RETRYING...", counter + 1)
		return ask_for(session, method, url, counter + 1, **kwargs)
	elif counter >= 2:
		print("CANNOT GET", url, r, sep="\n")
		raise Exception("Exception at request", r, url)
	return r


def clear_dir(folder):
	for the_file in os.listdir(folder):
		file_path = os.path.join(folder, the_file)
		try:
			if os.path.isfile(file_path):
				os.unlink(file_path)
			elif os.path.isdir(file_path):
				shutil.rmtree(file_path)
		except Exception as e:
			print(e)


def gstrftime(dt):
	s = dt.isoformat("T")
	return s


def gstrptime(iso_formatted_string):
	dt = iso8601.parse_date(iso_formatted_string)
	return dt


def tmp_save(txt, name, end="json"):
	unique_date = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
	with open("temp/" + f"{name}_{unique_date}.{end}", "w") as wf:
		if end == "json":
			json.dump(txt, wf, indent=4)
		else:
			wf.write(txt)
			wf.flush()


def progress_line(i, L, text, tab=30):
	n = int(((i + 1) / L) * tab)
	print("\r[", "=" * n, ">", " " * (tab - n - 1), "] ", i, " of ", L, " %s (%2.1f %%)" % (text, 100.0 * ((i) / L)),
	      sep="", end="")
