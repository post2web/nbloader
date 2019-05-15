import os
import io
from contextlib import contextmanager

import mistune

from nbformat import reader, converter, current_nbformat
from IPython.core.interactiveshell import InteractiveShell
from IPython import get_ipython
from IPython.core.compilerop import CachingCompiler

try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

@contextmanager
def temp_chdir(dir):
    cwd = os.getcwd()
    if dir and dir != cwd:
        os.chdir(dir)

    try:
        yield
    finally:
        if dir and dir != cwd:
            os.chdir(cwd)

class Notebook(object):

    blacklist = {'__skip__'}

    def __init__(self, nb_path, ns=None, tag_md=True, nb_dir=None,
                 close_blocks_at_headings=True, tag_marker='#'):
        '''

        Arguments:
            nb_path (str): the path to the notebook.
            ns (dict, optional): the namespace to use for the notebook. For a fresh namespace,
                leave as None (default). To share a namespace with the current notebook,
                pass in ns=globals().
            tag_md (bool): Use markdown headings as tags.
            nb_dir (str, optional): the directory to run commands from this notebook in.
            close_blocks_at_headings (bool): Implicitly close a block when a heading is reached.
                This only applies if tag_md == True.

        '''
        self.nb_path = nb_path
        self.nb_dir = os.path.dirname(nb_path) if nb_dir is None else nb_dir

        # markdown
        self.tag_md = tag_md
        self.close_blocks_at_headings = close_blocks_at_headings
        if tag_md:
            self.md_parser = mistune.Markdown()

        self.tag_marker = tag_marker
        assert tag_marker.strip()[0] == '#', 'tag markers must be in a comment'

        self.restart(ns)
        self.shell = get_ipython()
        self.refresh()
        self.run_tag('__init__', strict=False)

    def __repr__(self):
        return '<Notebook({}) {} cells, exec count: {} >'.format(
            self.nb_path, len(self.cells), self.exec_count)

    def summary(self, tag=None):
        for cell in self.cells:
            # TODO: print out hierarchy with cell count
            print(cell['tags'])

    def restart(self, ns=None):
        self.ns = ns or dict()
        self.exec_count = 0
        return self

    def refresh(self):
        self.cells = []
        self.md_tags = []
        self.block_tag = None

        with io.open(self.nb_path, 'r', encoding='utf-8') as f:
            notebook = reader.read(f)

        # convert to current notebook version
        notebook = converter.convert(notebook, current_nbformat)

        compiler = CachingCompiler()
        for i, cell in enumerate(notebook.cells):
            if cell.cell_type == 'markdown' and self.tag_md:
                # tokenize markdown block
                tokens = self.md_parser.block(cell.source)
                for tok in tokens:
                    if tok['type'] == 'heading':
                        # filter out smaller headings and add new heading
                        new_level, tag = tok['level'], tok['text']
                        self.md_tags = [
                            (lvl, tag) for lvl, tag in self.md_tags
                            if lvl < new_level
                        ]
                        self.md_tags.append((new_level, tag))

                        if self.close_blocks_at_headings: # new heading reached. Close block.
                            self.block_tag = None

            elif cell.cell_type == 'code':
                # translate all magic % commands to code
                source = self.shell.input_transformer_manager.transform_cell(cell.source)
                # need to use this cell_name so it gives a nice debug information from the notebook
                cell_name = compiler.cache(source, i)
                # compile the code
                source = compile(source, cell_name, 'exec')

                self.cells.append({'code': source, 'tags': self._cell_tags(cell)})

    def _run(self, cells):
        with temp_chdir(self.nb_dir):
            for cell in cells:
                exec(cell['code'], self.ns)
                self.exec_count += 1

                if HAS_MATPLOTLIB:
                    if plt.gcf().axes:
                        plt.show()
                    else:
                        plt.close()

    def _filter_blacklist(self, cells, blacklist=None):
        if blacklist is False: # disable blacklist
            blacklist = set()
        else:
            if isinstance(blacklist, str):
                blacklist = {blacklist}
            elif blacklist is None:
                blacklist = set()
            else:
                blacklist = set(blacklist)

            blacklist |= self.blacklist # merge blacklist

        return [
            cell for cell in self.cells
            if not any(tag in blacklist for tag in cell['tags'])
        ]

    def run_all(self, blacklist=None):
        cells = self._filter_blacklist(self.cells, blacklist)
        self._run(cells)
        return self

    def _cell_tags(self, cell):
        tags = cell.metadata.get('tags', [])

        for level, tag in self.md_tags:
            # can access either through heading text
            # or with level specified using markdown syntax
            tags.append(tag)
            tags.append('#' * level + ' ' + tag)

        if self.block_tag:
            tags.append(self.block_tag)

        if cell.cell_type == 'code':
            if cell.source and cell.source[0] == '#':
                first_line = cell.source.split('\n', 1)[0]

                if first_line.startswith('##block '): # start block ttag
                    first_line = first_line[8:].strip()
                    self.block_tag = first_line
                    tags.append(first_line)

                elif first_line.startswith('##lastblock'): # end block tag
                    self.block_tag = None

                else: # line tag
                    first_line = first_line.strip('#').strip()
                    tags.extend(first_line.split())

        return tags or [None]

    def run_tag(self, tag, strict=True, blacklist=None):
        cells = [cell for cell in self.cells if tag in cell['tags']]
        cells = self._filter_blacklist(cells, blacklist)

        if cells:
            self._run(cells)
        else:
            assert not strict, 'Tag "{}" found'.format(tag)
        return self

    def __del__(self):
        self.run_tag('__del__', strict=False)

    def __getstate__(self):
        return (self.nb_path, self.ns)

    def __setstate__(self, d):
        self.nb_path, self.ns = d

#
# class NotebookCells:
#
#     def __init__(self, cells, ns, nb_dir=None):
#         self.cells = cells
#         self.nb_dir = nb_dir
#
#     def __getitem__(self, k):
#         if isinstance(k, slice): # getting a range of tags
#             start, stop = k.start, k.stop
#             if not isinstance(start, str):
#                 start = self.get_tag_index(start)
#             if not isinstance(stop, str):
#                 stop = self.get_tag_index(stop)
#             k = slice(start, stop)
#             cells = self.cells[k]
#
#         elif isinstance(k, str): # getting a single tag
#             cells = [cell for cell in self.cells if tag in cell['tags']]
#         else:
#             raise KeyError('Key must be a tag')
#
#         return NotebookCells(cells, self.ns, self.nb_dir)
#
#     def get_tag_index(self, tag, end=False, strict=False):
#         try:
#             cells = self.cells if not end else self.cells[::-1]
#             i = next(i for i, cell in enumerate(cells) if tag in cell['tags'])
#             i = i if not end else -i
#         except StopIteration:
#             assert not strict, 'Tag "{}" found'.format(tag)
#             i = None
#         return i
#
#     def _run(self, cells):
#         cwd = os.getcwd()
#         if self.nb_dir:
#             os.chdir(self.nb_dir)
#
#         try:
#             for cell in cells:
#                 exec(cell['code'], self.ns)
#         finally:
#             os.chdir(cwd)
#
#     def run_all(self, blacklist=None):
#         if blacklist is False: # disable blacklist
#             blacklist = set()
#         else:
#             if isinstance(blacklist, str):
#                 blacklist = {blacklist}
#             elif blacklist is None:
#                 blacklist = set()
#             else:
#                 blacklist = set(blacklist)
#
#             blacklist |= self.blacklist # merge blacklist
#
#         cells = [
#             cell for cell in self.cells
#             if not any(tag in blacklist for tag in cell['tags'])
#         ]
#
#         self._run(cells)
#         return self
#
#     def run_tag(self, tag, strict=True):
#         cells = [cell for cell in self.cells if tag in cell['tags']]
#
#         if cells:
#             self._run(cells)
#         else:
#             assert not strict, 'Tag "{}" found'.format(tag)
#         return self
#
#     def run_before(self, tag, strict=True):
#         i = self.get_tag_index(tag, end=True, strict=strict)
#
#         if i:
#             self._run(cells[:i])
#         elif i is None:
#             assert not strict, 'Tag "{}" found'.format(tag)
#
#         return self
#
#     def run_after(self, tag, strict=True):
#         i = self.get_tag_index(tag, end=True, strict=strict)
#         if i:
#             self._run(cells[-i:])
#         elif i is None:
#             assert not strict, 'Tag "{}" found'.format(tag)
#         return self
