from ..blackarrow import index_worker

import pytest
import queue


@pytest.fixture
def results():
    input_queue = queue.Queue()
    index_worker(
        ['sample'],  # directories to look in
        None,  # things to ignore
        1,  # num workers
        input_queue,  # where to put results
        None,   # output (not needed)
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
