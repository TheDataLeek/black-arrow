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
        ignore_re = re.compile('a^') 
        if args.ignore:
            ignore_re = re.compile('|'.join(args.ignore))
        input = queue.Queue()
        output = queue.Queue()

        indexer = threading.Thread(name='indexer',
                                   target=index_worker,
                                   args=(args.directories,
                                         ignore_re,
                                         args.workers,
                                         input, output))
        indexer.start()
        for i in range(args.workers):
            t = threading.Thread(name='worker-{}'.format(i + 1),
                                 target=file_searching_worker,
                                 args=(re.compile(args.regex),
                                       input, output))
            t.start()
        printer = threading.Thread(name='printer',
                                   target=print_worker,
                                   args=(args.workers, output))
        printer.start()


def index_worker(directories: str, ignore_re: str, workers: int, input: queue.Queue, output: queue.Queue) -> None:
    file_count = 0
    for dir in directories:
        for dir, _, files in os.walk(dir):
            for question_file in files:
                filename = dir + '/' + question_file
                if ignore_re.search(filename) is None:
                    file_count += 1
                    input.put(filename)
    output.put(file_count)
    for i in range(workers):
        input.put('EXIT')  # poison pill workers


def file_searching_worker(regex: str, input: queue.Queue, output: queue.Queue) -> None:
    line_count = 0
    while True:
        name = input.get()
        if name == 'EXIT':
            output.put(('EXIT', line_count))
            break
        with open(name, 'r') as ofile:
            flag = []
            try:
                for i, line in enumerate(ofile.readlines()):
                    if regex.search(line):
                        flag.append((i, line.split('\n')[0]))
                line_count += i + 1
                if flag:
                    for value in sorted(flag, key=lambda tup:
                            regex.search(tup[1]).group(0)):
                        output.put('{}:{}{}{}\n\t{}'.format(name,
                            bcolors.OKGREEN, value[0], bcolors.ENDC,
                            insert_colour(value[1], regex)))
            except (UnicodeDecodeError, OSError, FileNotFoundError):
                pass


def print_worker(worker_count: int, output: queue.Queue) -> None:
    file_count = 0
    found_count = 0
    exit_count = 0
    line_count = 0
    while True:
        statement = output.get()
        if isinstance(statement, tuple):
            exit_count += 1
            line_count += statement[1]
            if exit_count == worker_count:
                break
        elif isinstance(statement, str):
            found_count += 1
            print(statement)
        else:
            file_count = statement

    print(('---------------\n'
           'Files Searched: {}\n'
           'Files Matched: {}\n'
           'Lines Searched: {}').format(file_count, found_count, line_count))


def insert_colour(str_to_add: str, regex: str) -> str:
    return re.sub('^[ \t]+', '', re.sub(regex, '{}\g<0>{}'.format(bcolors.WARNING, bcolors.ENDC), str_to_add))


def legacy(args: argparse.Namespace) -> None:
    ignore_re = re.compile('a^')
    if args.ignore != []:
        ignore_re = re.compile('|'.join(args.ignore))
    regex = re.compile(args.regex)

    file_counter = 0
    found_counter = 0
    line_counter = 0
    for dir in args.directories:
        for dir, dirs, files in os.walk(dir):
            for question_file in files:
                filename = dir + '/' + question_file
                if ignore_re.search(filename) is None:
                    file_counter += 1
                    with open(filename, 'r') as ofile:
                        flag = []
                        try:
                            for i, line in enumerate(ofile.readlines()):
                                if regex.search(line):
                                    flag.append((i, line.split('\n')[0]))
                            line_counter += i + 1
                            if flag:
                                found_counter += 1
                                for value in sorted(flag, key=lambda tup:
                                        regex.search(tup[1]).group(0)):
                                    print('{}:{}{}{}\n\t{}'.format(filename,
                                        bcolors.OKGREEN, value[0], bcolors.ENDC,
                                        insert_colour(value[1], args.regex)))
                        except UnicodeDecodeError:
                            pass
    print(('---------------\n'
           'Files Searched: {}\n'
           'Files Matched: {}\n'
           'Lines Searched: {}').format(file_counter, found_counter, line_counter))


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
