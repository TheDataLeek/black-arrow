#!/usr/bin/env python3.5

import argparse
import neovim
from ... import blackarrow

@neovim.plugin
class BlackArrow(object):
    def __init__(self, vim):
        self.vim = vim

    @neovim.command('BlackArrow', nargs=1)
    def search(self, args):
        self.vim.command('echo "{}"'.format(args))