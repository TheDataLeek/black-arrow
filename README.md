"Universal" Text Finder
=======================
It's basically just grep in python... Nothing fancy, just an easy extensible way
to find things....

Yeah, I know, it's "reinventing the wheel" but ehhh, this is easier to extend to
cover any and all weird cases without having to memorize a bunch of obscure
combinations of bash commands.

That out of the way, let's talk about what this *actually does*...

## Installation

Note, this is written in Python3.5, and uses type checking syntax.

I use [Vundle](https://github.com/VundleVim/Vundle.vim), but Pathogen or
whatever you want to use also works.

The script can also be used just as-is, just add it to your path.

## Black-Arrow Script

```bash
┬─[zoe@fillory:~/Dropbox/Projects/black-arrow]─[09:33:40 PM]
╰─>$ ./black-arrow/blackarrow.py -h
usage: blackarrow.py [-h] [-r REGEX] [-d DIRECTORIES [DIRECTORIES ...]]
                     [-i IGNORE [IGNORE ...]] [-f FILENAME [FILENAME ...]]
                     [-w WORKERS] [-p] [-e]
                     [R]

positional arguments:
  R                     Search term (regular expression)

optional arguments:
  -h, --help            show this help message and exit
  -r REGEX, --regex REGEX
                        Search term (regular expression)
  -d DIRECTORIES [DIRECTORIES ...], --directories DIRECTORIES [DIRECTORIES ...]
                        Director(y|ies) to run against
  -i IGNORE [IGNORE ...], --ignore IGNORE [IGNORE ...]
                        Things to ignore (regular expressions)
  -f FILENAME [FILENAME ...], --filename FILENAME [FILENAME ...]
                        Filename search term(s)
  -w WORKERS, --workers WORKERS
                        Number of workers to use (default 2)
  -p, --pipe            Run in "pipe" mode with brief output
  -e, --edit            Edit the files?
```

## Black-Arrow NeoVim Plugin






#### The Name

*"Arrow! Black arrow! I have saved you to the last. You have never failed me and
I have always recovered you. I had you from my father and he from of old. If
ever you came from the forges of the true king under the Mountain, go now and
speed well!"*

― J.R.R. Tolkien, The Hobbit
