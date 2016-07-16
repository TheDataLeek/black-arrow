#!/usr/bin/env python3

import neovim

@neovim.plugin
class Main(object):
    def __init__(self, vim):
        self.vim = vim

    @neovim.function('search')
    def search(self, args):
        self.vim.command('echo "hello"')

