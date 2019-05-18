import os
from contextlib import contextmanager



@contextmanager
def temp_chdir(directory):
    '''Temporarily change to another directory, then change back.
    Does nothing if the directory is empty.'''
    cwd = os.getcwd()
    if directory and directory != cwd:
        os.chdir(directory)

    try:
        yield
    finally:
        if directory and directory != cwd:
            os.chdir(cwd)

def get_tag_index(cells, tag, end=False, strict=False):
    '''Get the index of the first (or last) occurrence of a tag.'''
    try:
        return (next(i for i, cell in enumerate(cells) if tag in cell['tags'])
                if not end else
                -next(i for i, cell in enumerate(cells[::-1]) if tag in cell['tags'])
               ) or None
    except StopIteration:
        assert not strict, 'Tag "{}" found'.format(tag)
        return None

def filter_blacklist(cells, blacklist=None, default_blacklist=None):
    '''Filter out cells in both the class blacklist and the passed blacklist.

    Arguments:
        cells (list): list of cells to filter.
        blacklist (str|tuple|False, optional) the tags to filter out.
            If tuple, it will filter out each tag in the tuple as well as the
                classwide blacklist.
            If str, it is the same as passing `(str,)`
            If False, it will disable blacklist filtering.
            If None (default), it will only use the class blacklist.
        default_blacklist (tuple|None): the classwide/default blacklist to be merged.
    '''
    if blacklist is False: # disable blacklist
        blacklist = set()
    else:
        if isinstance(blacklist, str):
            blacklist = {blacklist}
        elif blacklist is None:
            blacklist = set()
        else:
            blacklist = set(blacklist)

        if default_blacklist:
            blacklist |= default_blacklist # merge blacklist with defaults

    return [
        cell for cell in cells
        if not any(tag in blacklist for tag in cell['tags'])
    ]
