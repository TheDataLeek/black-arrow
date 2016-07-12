#!/usr/bin/python3.5


import argparse
import sys
import os
import re
import multiprocessing as mp
import time
import subprocess
import curses


RETYPE = type(re.compile('a'))
EDITOR = os.environ.get('EDITOR', 'vim')


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
                               output, args.pipe, args.edit,
                               args.interactive))
    printer.start()
    printer.join()    # Wait main thread until printer is done


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
                            output.put((name, bcolors.OKGREEN,
                                value[0], bcolors.ENDC,
                                insert_colour(value[1], regex)))
            except:
                pass


def print_worker(start_time: float, worker_count: int, output: mp.Queue,
                 pipemode: bool, editmode: bool, interactivemode: bool) -> None:
    file_count = 0
    found_count = 0
    exit_count = 0
    line_count = 0
    file_list = []
    while True:
        statement = output.get()
        if not isinstance(statement[1], str):
            exit_count += 1
            line_count += statement[1]
            file_count += statement[2]
            found_count += statement[3]
            if exit_count == worker_count:
                break
        elif isinstance(statement[1], str):
            if pipemode:
                print(statement[0])
            else:
                print('{}:{}{}{}\n\t{}'.format(*statement))

                file_list.append((statement[2], statement[0]))

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
            print(bcolors.FAIL + 'Cowardly only accepting the first 10 files for editing' + bcolors.ENDC)
        call_string = '{} {}'.format(EDITOR, ' '.join(call_args[:10]))
        subprocess.call(call_string, shell=True)

    def interactive(stdscr):
        begin_x = 20
        begin_y = 7
        height = int(2 * len(file_list))
        width = 2 * max(file_list, key=lambda tup: len(str(tup)))[0]
        win = curses.newwin(height, width, begin_y, begin_x)

        pos = [0, 0]
        curses.setsyx(*pos)
        curses.curs_set(2)
        try:
            while True:
                i = 0
                stdscr.move(*pos)
                for linenum, filename in file_list:
                    stdscr.addstr(i, 0, filename, curses.A_NORMAL)
                    stdscr.addstr(i + 1, 0, str(linenum), curses.A_NORMAL)
                    i += 2
                stdscr.move(*pos)
                c = stdscr.getkey()
                if c == 'q':
                    break
                elif c == 'KEY_UP':
                    pos[0] = 0 if (pos[0] - 1) < 0 else pos[0] - 1
                elif c == 'KEY_DOWN':
                    pos[0] = height if (pos[0] + 1) > height else pos[0] + 1
                elif c == 'KEY_LEFT':
                    pos[1] = 0 if (pos[1] - 1) < 0 else pos[1] - 1
                elif c == 'KEY_RIGHT':
                    pos[1] = width if (pos[1] + 1) > width else pos[1] + 1
        except KeyboardInterrupt:
            pass

    if interactivemode:
        curses.wrapper(interactive)


def insert_colour(str_to_add: str, regex: RETYPE) -> str:
    return re.sub('^[ \t]+', '', re.sub(regex, '{}\g<0>{}'.format(bcolors.WARNING, bcolors.ENDC), str_to_add))


def get_args() -> argparse.Namespace:
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
    parser.add_argument('-w', '--workers', type=int, default=2,
                        help=('Number of workers to use (default 2)'))
    parser.add_argument('-p', '--pipe', action='store_true', default=False,
                        help=('Run in "pipe" mode with brief output'))
    parser.add_argument('-e', '--edit', action='store_true', default=False,
                        help=('Edit the files?'))
    parser.add_argument('-x', '--interactive', action='store_true', default=False,
                        help=('Run in Interactive Mode?'))
    args = parser.parse_args()
    args.regex = args.regex_positional if args.regex is None else args.regex
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
