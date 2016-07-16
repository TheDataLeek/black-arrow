import argparse
import neovim
from . import blackarrow


@neovim.plugin
class BlackArrow(object):
    def __init__(self, vim):
        self.vim = vim

    @neovim.command('BlackArrow', nargs='+')
    def search(self, args: str):
        self.vim.command('echo "{}"'.format(blackarrow.blackarrow.get_args(args)))
