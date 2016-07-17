import sys, os
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
        self.vim.command('set nomodifiable')
        self.vim.vars['buftype'] = 'nofile'

        self.vim.current.line = 'Finding {} in {}'.format(args.regex_positional, os.getcwd())

        printer, queue = blackarrow.start_search(args)

        i = 0
        while True:
            self.vim.command("echo 'here'")
            next_item = queue.get()
            if next_item == 'EXIT':
                break
            else:
                self.vim.current.buffer.append('{}) {}	{}'.format(i, *next_item))

