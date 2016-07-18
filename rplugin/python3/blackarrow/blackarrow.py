#!/usr/bin/python3.5

"""
Black-Arrow file keyword searcher
"""

import argparse
import sys
import os
import re
import multiprocessing as mp
import time
import subprocess
from typing import Optional
import fabulous.color as color


RETYPE = type(re.compile('a'))
EDITOR = os.environ.get('EDITOR', 'vim')


def main():
    args = get_args()
    print_process, final_queue = start_search(args)
    print_process.join()    # Wait main thread until printer is done


def start_search(args:argparse.Namespace):
    start_time = time.time()

    ignore_re = re.compile('a^')
    if args.ignore:
        ignore_re = re.compile('|'.join(args.ignore))
    filename_re = re.compile('.*')
    if args.filename:
        filename_re = re.compile('|'.join(args.filename))
    input = mp.Queue()
    output = mp.Queue()
    final_queue = mp.Queue()

    indexer = mp.Process(name='indexer',
                         target=index_worker,
                         args=(args.directories,
                               ignore_re,
                               args.workers,
                               input, output))
    indexer.start()

    for i in range(args.workers):
        worker = mp.Process(name='worker-{}'.format(i + 1),
                            target=file_searching_worker,
                            args=(re.compile(args.regex),
                                  ignore_re, filename_re,
                                  input, output))
        worker.start()
    printer = mp.Process(name='printer',
                         target=print_worker,
                         args=(start_time, args.workers,
                               output, final_queue, args.pipe, args.edit))
    printer.start()
    return printer, final_queue


def index_worker(directories: str, ignore_re: RETYPE, workers: int, input: mp.Queue, output: mp.Queue) -> None:
    for dir in list(set(directories)):  # no duplicates
        for subdir, _, files in os.walk(dir):
            for question_file in files:
                # we don't want to block, this process should be fastest
                input.put(subdir + '/' + question_file, block=False, timeout=10)  # faster than os.path.join
    for i in range(workers):
        input.put('EXIT')  # poison pill workers


def file_searching_worker(regex: RETYPE, ignore_re: RETYPE, filename_re: RETYPE, input: mp.Queue, output: mp.Queue) -> None:
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
                            output.put((name, value[0],  value[1], regex))
            except:
                pass


def print_worker(start_time: float, worker_count: int, output: mp.Queue, final_queue: mp.Queue,
                 pipemode: bool, editmode: bool) -> None:
    file_count  = 0
    found_count = 0
    exit_count  = 0
    line_count  = 0
    file_list   = []
    final_queue.put(('printing', 'job working'))
    while True:
        statement = output.get()
        if statement[0] == 'EXIT':
            exit_count += 1
            line_count += statement[1]
            file_count += statement[2]
            found_count += statement[3]
            if exit_count == worker_count:
                break
        else:
            final_queue.put(statement[0], statement[1])
            if pipemode:
                print('{}	{}	{}'.format(statement[0], statement[1], statement[2]))
            else:
                print('{}:{}\n\t{}'.format(statement[0],
                    color.fg256('#00ff00', statement[1]),
                    insert_colour(statement[2], statement[3])))

                file_list.append((statement[1], statement[0]))

    final_queue.put('EXIT')

    if not pipemode:
        print(('---------------\n'
               'Files Searched: {}\n'
               'Files Matched: {}\n'
               'Lines Searched: {}\n'
               'Duration: {}').format(file_count, found_count, line_count, time.time() - start_time))

    if editmode:
        files_to_edit = ['+{} {}'.format(num, name) for num, name in file_list]
        call_args = [_ for _ in files_to_edit[0].split(' ')]
        orientation = 0
        for f in files_to_edit[1:]:
            call_args.append('+"{} {}"'.format('sp' if orientation else 'vsp', f))
            orientation ^= 1
        if len(call_args) > 10:
            print(color.red('Cowardly only accepting the first 10 files for editing'))
        call_string = '{} {}'.format(EDITOR, ' '.join(call_args[:10]))
        subprocess.call(call_string, shell=True)


def insert_colour(str_to_add: str, regex: RETYPE) -> str:
    return re.sub('^[ \t]+', '', re.sub(regex, str(color.fg256('yellow', r'\g<0>')), str_to_add))


def get_args(manual_args: Optional[str]=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    regex_group = parser.add_mutually_exclusive_group(required=True)
    regex_group.add_argument('regex_positional', metavar='R', type=str, default=None, nargs='?',
                             help='Search term (regular expression)')
    regex_group.add_argument('-r', '--regex', type=str, default=None,
                             help='Search term (regular expression)')
    parser.add_argument('-d', '--directories', type=str, default=['.'], nargs='+',
                        help='Director(y|ies) to run against')
    parser.add_argument('-i', '--ignore', type=str, default=[], nargs='+',
                        help='Things to ignore (regular expressions)')
    parser.add_argument('-f', '--filename', type=str, default=[], nargs='+',
                        help='Filename search term(s)')
    parser.add_argument('-w', '--workers', type=int, default=4,
                        help=('Number of workers to use (default 2)'))
    parser.add_argument('-p', '--pipe', action='store_true', default=False,
                        help=('Run in "pipe" mode with brief output'))
    parser.add_argument('-e', '--edit', action='store_true', default=False,
                        help=('Edit the files?'))
    if manual_args is not None:
        args = parser.parse_args(args=manual_args)
    else:
        args = parser.parse_args()
    args.regex = args.regex_positional if args.regex is None else args.regex
    return args


if __name__ == '__main__':
    sys.exit(main())
