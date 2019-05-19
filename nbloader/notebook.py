import os
import io
import types
# import copy
from contextlib import contextmanager

import mistune
from nbformat import reader, converter, current_nbformat
from IPython import get_ipython
from IPython.core.interactiveshell import DummyMod, ExecutionResult, ExecutionInfo
from IPython.core.compilerop import CachingCompiler

from .utils import *

try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


class Notebook(object):

    blacklist = {'__skip__'}
    close_blocks_at_headings = True
    tag_marker = '##'

    def __init__(self, nb_path, ns=None, nb_dir=None,
                 init=True, tag_md=True,
                 ast_node_interactivity='none'):
        '''Load a Jupyter Notebook as an object.

        Arguments:
            nb_path (str): the path to the notebook.
            ns (dict, optional): the namespace to use for the notebook. For a fresh namespace,
                leave as None (default). To share a namespace with the current notebook,
                pass in ns=globals().
            init (bool): whether or not to run the __init__ tag automatically. Default True.
            tag_md (bool): Use markdown headings as tags. Default True.
            nb_dir (str, optional): the directory to run commands from this notebook in.
            close_blocks_at_headings (bool): Implicitly close a block when a heading is reached.
                This only applies if tag_md == True.

        '''
        # notebook source
        self.nb_path = nb_path
        self.nb_dir = os.path.dirname(nb_path) if nb_dir is None else nb_dir
        self.filename = os.path.splitext(os.path.basename(nb_path))[0]

        # markdown
        self.md_parser = mistune.Markdown() if tag_md else None

        # valid tag syntax
        assert self.tag_marker.strip()[0] == '#', 'tag markers must be a comment'

        # output
        self.auto_init = init

        # setup shell
        self.ast_node_interactivity = ast_node_interactivity
        self.shell = get_ipython()
        self.refresh()
        self.restart(ns)


    '''

    Summary

    '''

    def __repr__(self):
        return '<Notebook({}) {} cells, exec count: {} >'.format(
            self.nb_path, len(self.cells), self.exec_count)

    def summary(self, tag=None):
        '''Summarize all runnable cells.
        '''
        all_tags = [tag for cell in self.cells for l, tag in cell['md_tags']]

        heading, count = None, 0
        for cell in self.cells:
            # TODO: print out hierarchy with cell count properly
            if cell['md_tags'] != heading:
                if heading and count:
                    print('\t' * heading[-1][0] + '({} cells.)'.format(count))

                heading, count = cell['md_tags'], 1
                l, h = heading[-1]
                print('  '*(l-1) + '#'*l + ' ' + h)

            else:
                count += 1
        if heading:
            print('\t' * heading[-1][0] + '({} cells.)'.format(count))

    def var(self, *k, **kw):
        '''Helper to extract/set variables from the namespace.

        Example:
            ns = {'a': 1, 'b': 2, 'c': 3, 'd': 4}
            notebook = Notebook('example.ipynb', ns=ns)

            # getting
            a = notebook.var('a') # trivial
            a, b, c, d = notebook.var('a', 'b', 'c', 'd') # here's where it's convenient.
            assert (a, b) == (1, 2)

            # setting
            notebook.var(b=10) # shorthand for notebook.ns.update(dict(b=10))
            assert notebook.var('a', 'b') == (1, 10)
        '''
        # set
        for n, v in kw.items():
            self.ns[n] = v

        # get
        if len(k) == 1:
            return self.ns[k[0]]
        return tuple(self.ns[ki] for ki in k) or None

    '''

    Build Notebook

    '''

    def restart(self, ns=None):
        '''Simulate a notebook restart by clearing the namespace.

        Arguments:
            ns (dict, optional): the namespace to initialize with. Defaults to an empty dict.
        '''
        self.mod = mod = DummyMod()
        self.ns = mod.__dict__ = ns or dict()
        # sys.modules[self.filename] = mod

        with self._setup_environment():
            self.shell.init_user_ns() # add in all of the ipython history stuff into our ns

        self.exec_count = 0
        if self.auto_init:
            self.run_tag('__init__', strict=False)
        return self

    def refresh(self):
        '''Reload the notebook from file and compile cells.'''
        self.cells = []
        self.md_tags = []
        self.block_tag = None

        with io.open(self.nb_path, 'r', encoding='utf-8') as f:
            notebook = reader.read(f)

        # convert to current notebook version
        notebook = converter.convert(notebook, current_nbformat)

        compiler = CachingCompiler()
        for i, cell in enumerate(notebook.cells):
            if cell.cell_type == 'markdown' and self.md_parser:
                self._markdown_tags(cell)

            elif cell.cell_type == 'code' and cell.source:
                # translate all magic % commands to code
                source = self.shell.input_transformer_manager.transform_cell(cell.source)
                # need to use this cell_name so it gives a nice debug information from the notebook
                cell_name = compiler.cache(source, i)
                # compile the code
                source = compile(source, cell_name, 'exec')
                self.cells.append({'source': cell.source, 'code': source,
                                   'tags': self._cell_tags(cell),
                                   'md_tags': tuple(self.md_tags)})

        return self

    def _markdown_tags(self, cell):
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

    def _cell_tags(self, cell):
        '''Extract tags for a cell.'''
        tags = cell.metadata.get('tags', [])

        for level, tag in self.md_tags:
            # can access either through heading text
            # or with level specified using markdown syntax
            tags.append(tag)
            tags.append('#' * level + ' ' + tag)

        if self.block_tag:
            tags.append(self.block_tag)

        if cell.cell_type == 'code':
            if cell.source:
                first_line = cell.source.split('\n', 1)[0]

                if first_line.startswith('##block '): # start block tag
                    first_line = first_line[8:].strip()
                    self.block_tag = first_line
                    tags.append(first_line)

                elif first_line.startswith('##lastblock'): # end block tag
                    self.block_tag = None

                elif first_line.startswith(self.tag_marker): # line tag
                    first_line = first_line.strip('#').strip()
                    tags.extend(first_line.split())

        return tags or [None]

    '''

    Run Notebook

    '''

    @contextmanager
    def _setup_environment(self):
        '''Prepare the IPython environment to run cells from the loaded notebook.'''
        with temp_chdir(self.nb_dir): # possibly change directory
            try:
                # swap out ipython context vars
                orig_ns, self.shell.user_ns = self.shell.user_ns, self.ns
                # orig_mod, self.shell.user_module = self.shell.user_module, self.mod
                ast_node_interactivity, self.shell.ast_node_interactivity = (
                    self.shell.ast_node_interactivity, self.ast_node_interactivity)
                yield
            finally:
                # swap values back
                self.shell.user_ns = orig_ns
                # self.shell.user_mod = orig_mod
                self.shell.ast_node_interactivity = ast_node_interactivity

    def _execute_cell(self, cell):
        '''Execute a single cell.'''
        print(cell['source'])
        exec(cell['code'], self.ns)

        if HAS_MATPLOTLIB:
            if plt.gcf().axes:
                plt.show()
            else:
                plt.close()
        return ExecutionResult(ExecutionInfo(cell['source'], False, False, False))

        # See: https://github.com/ipython/ipython/blob/b70b3f21749ca969088fdb54edcc36bb8a2267b9/IPython/core/interactiveshell.py#L2801
        # result = self.shell.run_cell(cell['source'])
        # self.exec_count += 1
        return result

    def _iter_cells(self, cells, raise_exceptions=False):
        '''Run each cell yield in between each one.'''
        with self._setup_environment():
            for cell in cells:
                yield cell

    def _run(self, cells, **kw):
        '''Run all cells passed.'''
        for cell in self._iter_cells(cells, **kw):
            result = self._execute_cell(cell)
            if result.error_in_exec and not isinstance(result.error_in_exec, GeneratorExit):
                result.raise_error()
                break

        return self


    def run_all(self, blacklist=None, **kw):
        '''Run all cells (excluding those in the blacklist).'''
        cells = filter_blacklist(self.cells, blacklist, self.blacklist)
        self._run(cells, **kw)
        return self

    def run_tag(self, tag, strict=True, blacklist=None, **kw):
        '''Run all cells matching a tag.'''
        if isinstance(tag, str):
            tag = (tag,)
        cells = [cell for cell in self.cells if all(t in cell['tags'] for t in tag)]
        assert cells or not strict, 'Tag {} found'.format(tag)

        cells = filter_blacklist(cells, blacklist, self.blacklist, tag)
        self._run(cells, **kw)
        return self

    def run_before(self, tag, include=False, strict=True, blacklist=None, **kw):
        '''Run all cells before a tag.'''
        i = get_tag_index(self.cells, tag, end=include, strict=strict)

        if i: # otherwise, there's nothing before
            cells = filter_blacklist(self.cells[:i], blacklist, self.blacklist)
            self._run(cells, **kw)
        return self

    def run_after(self, tag, include=True, strict=True, blacklist=None, **kw):
        '''Run all cells after a matching tag.'''
        i = get_tag_index(self.cells, tag, end=not include, strict=strict)

        if i: # otherwise, there's nothing after
            cells = filter_blacklist(self.cells[i:], blacklist, self.blacklist)
            self._run(cells, **kw)
        return self

    '''

    Utils/Housekeeping

    '''

    # def __getitem__(self, k):
    #     if isinstance(k, slice): # getting a range of tags
    #         start, stop = k.start, k.stop
    #         start = get_tag_index(self.cells, start) if start is not None else None
    #         stop = get_tag_index(self.cells, stop) if stop is not None else None
    #         cells = self.cells[start:stop]
    #
    #     elif isinstance(k, str): # getting a single tag
    #         cells = [cell for cell in self.cells if tag in cell['tags']]
    #
    #     else:
    #         raise KeyError('Key must be a tag')
    #
    #     sliced_nb = copy.copy(self)
    #     sliced_nb.cells = cells
    #     return sliced_nb

    def __del__(self):
        self.run_tag('__del__', strict=False)

    def __getstate__(self):
        return self.nb_path, self.ns

    def __setstate__(self, d):
        self.nb_path, self.ns = d
