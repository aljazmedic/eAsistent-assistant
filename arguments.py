import argparse


def args_program_init():
	parser = argparse.ArgumentParser()
	parser.add_argument('--prune_temp', '-p', help='prune temp folder', action='store_true')
	parser.add_argument('--cname', help="Calendar name (defaults to School2)", dest="cal_name", type=str, default="School2")
	parser.add_argument('--rm_cal', '-rc', help="Removes the calendar befor running.", dest="rm_cal", required=False, action='store_true')
	return parser.parse_args()


def run_args_init():
	parser = argparse.ArgumentParser()
	parser.add_argument('--prune_temp', '-p', help='Prune temp folder', action='store_false')
	parser.add_argument('--cname', help="Calendar name (defaults to School2)", dest="cal_name", type=str, default="School2")
	parser.add_argument('--rm_cal', '-rc', help="Removes the calendar befor running.", dest="rm_cal", required=False, action='store_false')
	parser.add_argument('--file', '-f', help="Log file name.", dest="log_file_name", required=False, type=str, default='logs/%s.log')
	parser.add_argument('--log_type', help="Log Mode. Either append or write.", dest="log_mode", required=False, choices=['w', 'a'], type=str, default='w')

	return parser.parse_args()
