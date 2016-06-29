#!/usr/bin/python3.5


import argparse
import sys
import os
import re
import threading
import queue


def main():
    args = get_args()

    if args.legacy:
        legacy(args)
    else:
        ignore_re = None if args.ignore == [] else '|'.join(args.ignore)
        input = queue.Queue()
        output = queue.Queue()

        indexer = threading.Thread(target=index_worker, args=(args.directories, ignore_re, args.workers, input, output))
        indexer.start()
        indexer.join()
        workers = []
        for i in range(args.workers):
            t = threading.Thread(target=file_searching_worker, args=(args.regex, input, output))
            workers.append(t)
            t.start()
        printer = threading.Thread(target=print_worker, args=(args.workers, output))
        printer.start()
        printer.join()
        [t.join() for t in workers]


def index_worker(directories: str, ignore_re: str, workers: int, input: queue.Queue, output: queue.Queue) -> None:
    file_count = 0
    for dir in directories:
        for dir, dirs, files in os.walk(dir):
            # will short circuit
            clean_files = [os.path.join(dir, f)
                           for f in files
                           if (ignore_re is None) or
                               (re.search(ignore_re, os.path.join(dir, f)) is None)]
            for name in clean_files:
                file_count += 1
                input.put(name)
    output.put(file_count)
    for i in range(workers):
        input.put('EXIT')  # poison pill workers


def file_searching_worker(regex: str, input: queue.Queue, output: queue.Queue) -> None:
    while True:
        name = input.get()
        if name == 'EXIT':
            output.put('EXIT')
            break
        with open(name, 'r') as ofile:
            flag = []
            try:
                for i, line in enumerate(ofile.readlines()):
                    if re.search(regex, line):
                        flag.append((i, line.split('\n')[0]))
                if flag != []:
                    for v in sorted(flag, key=lambda tup: re.search(regex, tup[1]).group(0)):
                        output.put('{}:{}{}{}\n\t{}'.format(name,
                            bcolors.OKGREEN, v[0], bcolors.ENDC,
                            insert_colour(v[1], regex)))
            except (UnicodeDecodeError, OSError, FileNotFoundError):
               pass


def print_worker(worker_count: int, output: queue.Queue) -> None:
    file_count = 0
    found_count = 0
    exit_count = 0
    while True:
        statement = output.get()
        if statement == 'EXIT':
            exit_count += 1
            if exit_count == worker_count:
                break
        elif isinstance(statement, str):
            found_count += 1
            print(statement)
        else:
            file_count = statement

    print(('---------------\n'
           'Files Searched: {}\n'
           'Files Matched: {}').format(file_count, found_count))


def insert_colour(str_to_add: str, regex: str) -> str:
    return re.sub('^[ \t]+', '', re.sub(regex, '{}\g<0>{}'.format(bcolors.WARNING, bcolors.ENDC), str_to_add))


def legacy(args: argparse.Namespace) -> None:
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


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--directories', type=str, default=['.'], nargs='+',
                        help='Director(y|ies) to run against')
    parser.add_argument('-r', '--regex', type=str, default=None,
                        help='Search term (regular expression)')
    parser.add_argument('-i', '--ignore', type=str, default=[], nargs='+',
                        help='Things to ignore (regular expressions)')
    parser.add_argument('-w', '--workers', type=int, default=2,
                        help=('Number of workers to use (default 2)'))
    parser.add_argument('-l', '--legacy', action='store_true', default=False,
                        help='Run in "legacy mode"')
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
