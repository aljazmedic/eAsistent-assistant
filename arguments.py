#!/usr/bin/python3
import argparse
import logging


def run_args_init():
	parser = argparse.ArgumentParser()
	parser.add_argument('--prune_temp', '-p', help='Prune temp folder', default=False, action='store_true')
	parser.add_argument('--cname', help="Calendar name (defaults to School2)", dest="cal_name", type=str, default="School2")
	parser.add_argument('--rm_cal', '-rc', help="Removes the calendar befor running.", dest="rm_cal", action='store_true', default=False)
	parser.add_argument('--file', '-f', help="Log file name.", dest="log_file_name", type=str, default='%s.log')
	parser.add_argument('--log_type', help="Log Mode. Either append or write.", dest="log_mode", choices=['w', 'a'], type=str, default='a')
	parser.add_argument('--log_dir', help="Log Dir.", dest="log_dir", type=str, default='logs/')
	parser.add_argument('--days', '-d', nargs='+', help='Relative days', dest="days", default=None, required=False)
	parser.add_argument('--meals', '-m', help='Configure meals', default=False, action='store_true')
	dbg_level_group = parser.add_mutually_exclusive_group()
	dbg_level_group.add_argument('--verbose', '-v', action="store_const", const=logging.DEBUG, dest="log_level", default=logging.INFO)
	dbg_level_group.add_argument('--quiet', '-q', action="store_const", const=logging.WARNING, dest="log_level", default=logging.INFO)
	return parser.parse_args()
