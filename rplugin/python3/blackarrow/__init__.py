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

        actualstdout = sys.stdout
        sys.stdout = io.StringIO()

        self.vim.command('vnew')
        self.vim.command('set buftype=nofile') # make this non-editable

        printer = blackarrow.start_search(args)
        printer.join()

        self.vim.current.line = sys.stdout.getvalue()

