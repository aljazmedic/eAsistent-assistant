import argparse


def arg_init():
	parser = argparse.ArgumentParser()
	parser.add_argument('--prune_temp', '-p', help='prune temp folder', action='store_true')
	parser.add_argument('--calendar_name', help="Calendar name (defaults to School2)", dest="cal_name", type=str, default="School2")
	parser.add_argument('--remove_calendar', help="Removes the calendar befor running.", dest="rm_cal", required=False, action='store_true')
	return parser.parse_args()
