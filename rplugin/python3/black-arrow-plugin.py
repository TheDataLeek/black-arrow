#!/usr/bin/env python3.5

import neovim

print('here')

@neovim.plugin
class BlackArrow(object):
    def __init__(self, vim):
        print('test')
        self.vim = vim

    @neovim.function('BlackArrow', sync=True)
    def search(self, args):
        self.vim.command('echo "hello"')
        return 5

