from ..blackarrow import index_worker

import os
import pytest
import glob
import multiprocessing as mp


@pytest.fixture
def results():
    input_queue = mp.Queue()
    index_worker('sample', None, 1, input_queue, None)

    vals = []
    while not input_queue.empty():
        vals.append(input_queue.get())
    return vals


def test_not_empty(results):
    assert len(results) != 0


def test_correct_results(results):
    assert False
