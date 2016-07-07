#!/usr/bin/python3.5


import argparse
import sys
import os
import re
import multiprocessing as mp
import time


def main():
    args = get_args()

    start_time = time.time()

    ignore_re = re.compile('a^')
    if args.ignore:
        ignore_re = re.compile('|'.join(args.ignore))
    filename_re = re.compile('.*')
    if args.filename:
        filename_re = re.compile('|'.join(args.filename))
    input = mp.Queue()
    output = mp.Queue()

    mp.Process(name='indexer',
               target=index_worker,
               args=(args.directories,
                     ignore_re,
                     args.workers,
                     input, output)).start()

    for i in range(args.workers):
        mp.Process(name='worker-{}'.format(i + 1),
                   target=file_searching_worker,
                   args=(re.compile(args.regex),
                         ignore_re, filename_re,
                         input, output)).start()
    printer = mp.Process(name='printer',
                         target=print_worker,
                         args=(start_time, args.workers, output))
    printer.start()
    printer.join()    # Wait main thread until printer is done


def index_worker(directories: str, ignore_re: str, workers: int, input: mp.Queue, output: mp.Queue) -> None:
    for dir in list(set(directories)):  # no duplicates
        for subdir, _, files in os.walk(dir):
            for question_file in files:
                # we don't want to block, this process should be fastest
                input.put(subdir + '/' + question_file, block=False, timeout=10)  # faster than os.path.join
    for i in range(workers):
        input.put('EXIT')  # poison pill workers


def file_searching_worker(regex: str, ignore_re: str, filename_re: str, input: mp.Queue, output: mp.Queue) -> None:
    line_count = 0
    file_count = 0
    found_count = 0
    # https://stackoverflow.com/questions/566746/how-to-get-console-window-width-in-python
    rows, columns = os.popen('stty size', 'r').read().split()
    maxwidth = int(3 * int(columns) / 4)
    while True:
        # we want to block this thread until we get input
        name = input.get()
        if name == 'EXIT':
            output.put(('EXIT', line_count, file_count, found_count))
            break
        if ignore_re.search(name) is None and filename_re.search(name) is not None:
            file_count += 1
            try:
                with open(name, 'r') as ofile:
                    flag = []
                    i = 1
                    for line in ofile:
                        if regex.search(line):
                            found_string = line.split('\n')[0]
                            if len(found_string) > maxwidth:
                                found_string = found_string[:maxwidth] + '...'
                            flag.append((i, found_string))
                        i += 1
                    line_count += i
                    if flag:
                        found_count += 1
                        for value in flag:
                            output.put('{}:{}{}{}\n\t{}'.format(name,
                                bcolors.OKGREEN, value[0], bcolors.ENDC,
                                insert_colour(value[1], regex)))
            except:
                pass


def print_worker(start_time: float, worker_count: int, output: mp.Queue) -> None:
    file_count = 0
    found_count = 0
    exit_count = 0
    line_count = 0
    while True:
        statement = output.get()
        if isinstance(statement, tuple):
            exit_count += 1
            line_count += statement[1]
            file_count += statement[2]
            found_count += statement[3]
            if exit_count == worker_count:
                break
        elif isinstance(statement, str):
            print(statement)

    print(('---------------\n'
           'Files Searched: {}\n'
           'Files Matched: {}\n'
           'Lines Searched: {}\n'
           'Duration: {}').format(file_count, found_count, line_count, time.time() - start_time))


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
    parser.add_argument('-f', '--filename', type=str, default=[], nargs='+',
                        help='Filename search term(s)')
    parser.add_argument('-w', '--workers', type=int, default=2,
                        help=('Number of workers to use (default 2)'))
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
