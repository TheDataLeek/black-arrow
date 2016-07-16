#!/usr/bin/env python3.5

import neovim

@neovim.plugin
class BlackArrow(object):
    def __init__(self, vim):
        self.vim = vim

    @neovim.autocmd('BlackArrow')
    def search(self):
        self.vim.command('echo "hello"')
        return 10
