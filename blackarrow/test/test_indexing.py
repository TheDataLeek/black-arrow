from ..blackarrow import index_worker

import re
import pytest
import queue


@pytest.fixture
def results():
    """
    def index_worker(
        directories: List[str],
        ignore_re: RETYPE,
        filename_re: RETYPE,
        workers: int,
        search_queue: mp.Queue,
        depth: int,
        block=False,
    ) -> None:
    :return:
    """
    input_queue = queue.Queue()
    index_worker(
        ['sample'],  # directories to look in
        re.compile("a^"), # things to ignore
        re.compile('test'),  # things to search for
        1,  # num workers
        input_queue,  # where to put results
        None,   # depth (not needed)
        block=True   # whether or not to block
    )

    vals = []
    while not input_queue.empty():
        vals.append(input_queue.get())
    return vals


def test_not_empty(results):
    assert len(results) != 0


def test_correct_results(results):
    assert (
        len(
            set(results).difference(
                {'sample/tester.txt',
                 'sample/tester2.txt',
                 'EXIT'}
            )
        ) == 0
    )
