import os
from functools import wraps
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
    if isinstance(tag, str):
        tag = (tag,)

    try:
        return (next(i for i, cell in enumerate(cells)
                     if all(t in cell['tags'] for t in tag))
                if not end else
                -next(i for i, cell in enumerate(cells[::-1])
                      if all(t in cell['tags'] for t in tag))
               ) or None
    except StopIteration:
        assert not strict, 'Tag "{}" found'.format(tag)
        return None

def filter_blacklist(cells, blacklist=None, default_blacklist=None, include=None):
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
        include (tuple|None): items to remove from the blacklist.
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

        if include:
            blacklist -= set(include)

    return [
        cell for cell in cells
        if not any(tag in blacklist for tag in cell['tags'])
    ]



def refresh_prior(func):
    @wraps(func)
    def inner(self, *a, **kw):
        if self.autorefresh:
            self.refresh(on_changed=True)
        return func(self, *a, **kw)
    return inner

# class ObjectView:
#     '''Wraps around another object and overrides properties that have been set on the view.'''
#     def __init__(self, source, **kw):
#         self.source
#         for k, v in kw.items():
#             setattr(self, k, v)
#
#     def __getattr__(self, name):
#         return getattr(self.source, name)
#
