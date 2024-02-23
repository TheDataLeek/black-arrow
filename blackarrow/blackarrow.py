#!/usr/bin/env python3

"""
Black-Arrow file keyword searcher

Python3.5+
"""

import argparse
import os
import re
import multiprocessing as mp
import time
import subprocess
import fabulous.color as color
from faster_fifo import Queue

from typing import List, Union


RETYPE = type(
    re.compile("a")
)  # since re module apparently doesn't have good compiled types
EDITOR = os.environ.get("EDITOR", "nvim")  # Default editor
DEVMODE = False
QUEUE_SIZE = 5_000_000
WORKER_CHUNK_SIZE = 10_000
PRINT_CHUNK_SIZE = 100


def start_search(args: argparse.Namespace):
    """
    This function is separated out in order to use code as module
    """
    global DEVMODE
    DEVMODE = args.dev

    start_time = time.time()

    args.ignore = args.ignore + ["build", "\.min\.js", ".git"]

    # compile for performance reasons
    try:
        ignore_re = re.compile("a^")
        if args.ignore:
            ignore_re = re.compile("|".join(args.ignore))
        filename_re = re.compile(".*")
        if args.filename:
            filename_re = re.compile("|".join(args.filename))

        if args.lower or args.regex != args.regex.lower():
            search_re = re.compile(args.regex)
        else:
            search_re = re.compile(args.regex, flags=re.IGNORECASE)
    except re.error as e:
        print(color.red("Error, bad regular expression:"))
        raise

    # get numworkers
    # default to numcores
    # backup is 6 or specified by user
    try:
        numworkers = mp.cpu_count()
    except NotImplementedError:
        numworkers = args.workers or 6

    mp.set_start_method('fork')

    search_queue = Queue(QUEUE_SIZE)
    output = Queue(QUEUE_SIZE)
    final_queue = Queue(QUEUE_SIZE)  # Use final queue for external output
    processes = []

    indexer = mp.Process(
        name="indexer",
        target=index_worker,
        args=(
            args.directories,
            ignore_re,
            filename_re,
            numworkers,
            search_queue,
            args.depth,
        ),
    )
    indexer.start()
    processes.append(indexer)

    for i in range(numworkers):
        worker = mp.Process(
            name=f"worker-{i + 1}",
            target=file_searching_worker,
            args=(i, search_re, args.replace, search_queue, output),
        )
        worker.start()
        processes.append(worker)
    printer = mp.Process(
        name="printer",
        target=print_worker,
        args=(start_time, numworkers, output, final_queue, args.pipe, args.edit, args.match_only),
    )
    printer.start()
    processes.append(printer)

    return processes, final_queue


def index_worker(
    directories: List[str],
    ignore_re: RETYPE,
    filename_re: RETYPE,
    workers: int,
    search_queue: Queue,
    depth: int,
) -> None:
    for dir in list(set(directories)):  # no duplicates
        for subdir, folders, files in os.walk(dir):
            # if depth exceeds the required depth, do not walk deeper
            if depth is not None and subdir.count(os.sep) >= depth:
                del folders[:]

            search_queue.put_many([
                subdir + "/" + question_file # faster than os.path.join
                for question_file in files
                if (filename_re.search(question_file) is not None)  # should we search?
                and (ignore_re.search(question_file) is None)    # do we ignore?
            ])
    # for i in range(workers):
    search_queue.put("EXIT")  # poison pill workers


def file_searching_worker(
    worker_num: int, regex: RETYPE, replace: Union[str, None], search_queue: Queue, output: Queue
) -> None:
    line_count = 0
    file_count = 0
    found_count = 0
    while True:
        # we want to block this thread until we get search_queue
        names = search_queue.get_many(block=True, max_messages_to_get=WORKER_CHUNK_SIZE, timeout=10)
        for name in names:
            if name == "EXIT":
                output.put(("EXIT" + str(worker_num), line_count, file_count, found_count))
                search_queue.put("EXIT")
                return

            file_count += 1
            try:
                new_text = None
                with open(name, "r") as ofile:
                    matched_lines = []
                    i = 1
                    for line in ofile:
                        match = regex.search(line)
                        if match:
                            matched_lines.append((i, line.strip(), match.group(0)))
                        i += 1
                    line_count += i
                    found_count += len(matched_lines)
                    for value in matched_lines:
                        if replace is not None:
                            output.put((name, *value, regex, replace))
                        else:
                            output.put((name, *value, regex))
                    if replace is not None:
                        ofile.seek(0)  # reset to beginning
                        new_text = regex.subn(replace, ofile.read())[0]
                if replace is not None:
                    with open(name, "w") as ofile:
                        ofile.write(new_text)
            except:
                pass


def print_worker(
    start_time: float,
    worker_count: int,
    output: Queue,
    final_queue: Queue,
    pipemode: bool,
    editmode: bool,
    match_only: bool,
) -> None:
    file_count = 0
    found_count = 0
    exit_count = 0
    line_count = 0
    file_list = []
    death_flag = False
    # https://stackoverflow.com/questions/566746/how-to-get-console-window-width-in-python
    rows, columns = os.popen("stty size", "r").read().split()
    # Max width of printed line is 3/4 column count
    maxwidth = int(3 * int(columns) / 4)
    while True:
        if death_flag:
            break
        all_statements = output.get_many(block=True, timeout=60, max_messages_to_get=PRINT_CHUNK_SIZE)
        for statement in all_statements:
            if statement[0][:4] == "EXIT":
                exit_count += 1
                line_count += statement[1]
                file_count += statement[2]
                found_count += statement[3]

                if DEVMODE:
                    print(statement[0])
                    print(exit_count, worker_count)

                if exit_count == worker_count:
                    death_flag = True

            else:
                if len(statement) == 5:
                    filename, linenum, matched_line, matched, regex = statement
                    replace = None
                else:
                    filename, linenum, matched_line, matched, regex, replace = statement

                if not DEVMODE:
                    all_groups = []
                    for match in regex.finditer(matched_line):
                        all_groups += list(match.groups())
                    all_groups = ','.join(all_groups)
                    if pipemode:
                        line_to_print = f"{filename}|{linenum}|{matched}|{matched_line}|{all_groups}"
                    else:
                        if len(matched_line) > maxwidth:
                            matched_line = matched_line[:maxwidth] + "..."
                        if all_groups:
                            matched += f'\n\t[{all_groups}]'
                        line_to_print = (
                            f"{filename}:{color.fg256('#00ff00', linenum)}"
                            f"\n\t{insert_colour(matched_line, regex, extra_str=replace)}"
                        )

                        file_list.append((statement[1], statement[0]))

                    print(line_to_print)

    final_queue.put("EXIT")

    if not pipemode:
        runtime = time.time() - start_time
        print(
                "---------------\n"
                f"Files Searched: {file_count:,}\n"
                f"Files Matched: {found_count:,}\n"
                f"Lines Searched: {line_count:,}\n"
                f"Duration: {runtime:.3f}"
        )

    if editmode:
        files_to_edit = [f"+{num} {name}" for num, name in file_list]
        call_args = [_ for _ in files_to_edit[0].split(" ")]
        orientation = 0
        for f in files_to_edit[1:]:
            call_args.append('+"{} {}"'.format("sp" if orientation else "vsp", f))
            orientation ^= 1
        if len(call_args) > 10:
            print(color.red("Cowardly only accepting the first 10 files for editing"))
        call_string = "{} {}".format(EDITOR, " ".join(call_args[:10]))
        subprocess.call(call_string, shell=True)


def insert_colour(matchstring: str, regex: RETYPE, extra_str=None) -> str:
    """
    Given some string and a regex, color the match inside that string

    :param matchstring:
    :param regex:
    :param extra_str:
    :return:
    """
    if extra_str is None:
        replace_str = str(color.fg256("yellow", r"\g<0>"))
    else:
        replace_str = str(color.fg256("yellow", r"(\g<0> -> {})".format(extra_str)))
    return re.sub("^[ \t]+", "", re.sub(regex, replace_str, matchstring))
