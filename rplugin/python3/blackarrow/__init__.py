import sys
import io
import argparse
import neovim
from . import blackarrow


# TODO: integrate with netrw


@neovim.plugin
class BlackArrow(object):
    def __init__(self, vim):
        self.vim = vim

    @neovim.command('BlackArrow', nargs='+', sync=False)
    def search(self, args: str):
        args = blackarrow.get_args(args)   # args: argparse.Namespace
        args.pipe = False
        args.edit = False

        self.vim.command('vnew')
        self.vim.command('vertical resize 30')

        # self.vim.vars['netrw_list_hide'] = '.*'

        printer, queue = blackarrow.start_search(args)

        while True:
            next_item = queue.get()
            if next_item == 'EXIT':
                break
            else:
                self.vim.current.line = '{}	{}'.format(*next_item)

