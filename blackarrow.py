#!/usr/bin/python3.5


import argparse
import sys
import os
import re


def main():
    args = get_args()

    ignore_re = None if args.ignore == [] else '|'.join(args.ignore)

    file_counter = 0
    found_counter = 0
    for dir in args.directories:
        for dir, dirs, files in os.walk(dir):
            # will short circuit
            clean_files = [os.path.join(dir, f)
                           for f in files
                           if (ignore_re is None) or
                               (re.search(ignore_re, os.path.join(dir, f)) is None)]
            for name in clean_files:
                file_counter += 1
                with open(name, 'r') as ofile:
                    flag = []
                    try:
                        for i, line in enumerate(ofile.readlines()):
                            if re.search(args.regex, line):
                                flag.append((i, line.split('\n')[0]))
                        if flag != []:
                            found_counter += 1
                            for v in sorted(flag, key=lambda tup: re.search(args.regex, tup[1]).group(0)):
                                print('{}:{}{}{}\n\t{}'.format(name,
                                    bcolors.OKGREEN, v[0], bcolors.ENDC,
                                    insert_colour(v[1], args.regex)))
                    except UnicodeDecodeError:
                       pass
    print(('---------------\n'
           'Files Searched: {}\n'
           'Files Matched: {}').format(file_counter, found_counter))


def insert_colour(str_to_add: str, regex: str) -> str:
    return re.sub('^[ \t]+', '', re.sub(regex, '{}\g<0>{}'.format(bcolors.WARNING, bcolors.ENDC), str_to_add))


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--directories', type=str, default=['.'], nargs='+',
                        help='Director(y|ies) to run against')
    parser.add_argument('-r', '--regex', type=str, default=None,
                        help='Search term (regular expression)')
    parser.add_argument('-i', '--ignore', type=str, default=[], nargs='+',
                        help='Things to ignore (regular expressions)')
    args = parser.parse_args()
    if args.regex is None:
        print('Must supply a search string!')
        sys.exit(0)
    return args


class bcolors:
    """ http://stackoverflow.com/questions/287871/print-in-terminal-with-colors-using-python """
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


if __name__ == '__main__':
    sys.exit(main())
