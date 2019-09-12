import argparse
from typing import Optional

from . import blackarrow as ba


def main():
    args = get_args()
    processes, final_queue = ba.start_search(args)
    try:
        # This doesn't work as it is hanging on that queue for memory safety
        # print_process.join()  # Wait main thread until printer is done

        # need to instead listen to that queue and treat it as poison - like the others
        while True:
            poison = final_queue.get()
            if poison == 'EXIT':
                break

    except (KeyboardInterrupt, EOFError):  # kill all on ctrl+c/d
        [p.terminate() for p in processes]


def get_args(manual_args: Optional[str] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    regex_group = parser.add_mutually_exclusive_group(required=True)
    regex_group.add_argument(
        "regex_positional",
        metavar="R",
        type=str,
        default=None,
        nargs="?",
        help="Search term (regular expression)",
    )
    parser.add_argument(
        "-d",
        "--directories",
        type=str,
        default=["."],
        nargs="+",
        help="Director(y|ies) to run against",
    )
    parser.add_argument(
        "-i",
        "--ignore",
        type=str,
        default=[],
        nargs="+",
        help="Things to ignore (regular expressions)",
    )
    parser.add_argument(
        "-f",
        "--filename",
        type=str,
        default=[],
        nargs="+",
        help="Filename search term(s)",
    )
    parser.add_argument(
        "-w",
        "--workers",
        type=int,
        default=None,
        help=("Number of workers to use (default numcores, with fallback 6 unless set)"),
    )
    parser.add_argument(
        "-p",
        "--pipe",
        action="store_true",
        default=False,
        help=('Run in "pipe" mode with brief output'),
    )
    parser.add_argument(
        "-e", "--edit", action="store_true", default=False, help=("Edit the files?")
    )
    parser.add_argument(
        "-l",
        "--lower",
        action="store_true",
        default=False,
        help=("Check strict lower case?"),
    )
    parser.add_argument(
        "-r",
        "--replace",
        type=str,
        default=None,
        help="Replace text found in place with supplied",
    )
    parser.add_argument(
        "-D",
        "--depth",
        type=int,
        default=None,
        required=False,
        help="Directory depth to search in",
    )
    parser.add_argument(
        "--dev",
        action="store_true",
        default=False,
        help=("Run in development mode (NO OUTPUT)"),
    )

    if manual_args is not None:
        args = parser.parse_args(args=manual_args)
    else:
        args = parser.parse_args()
    args.regex = args.regex_positional
    return args
