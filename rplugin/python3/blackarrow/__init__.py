import sys
import io
import argparse
import neovim
from . import blackarrow


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

        # blackarrow.start_search(args)
        # self.vim.out_write(sys.stdout.getvalue())

        self.vim.current.Buffer[:] = 'test string 28973245987'
