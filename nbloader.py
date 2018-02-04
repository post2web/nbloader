import os
import io

from nbformat import reader, converter, current_nbformat
from IPython.core.interactiveshell import InteractiveShell
from IPython import get_ipython
from IPython.core.compilerop import CachingCompiler

class NotImplementedError(Exception):
    pass

class Notebook(object):
    
    def __init__(self, nb_path, ns=None):
        self.nb_path = nb_path
        if ns is None:
            self.ns = dict()
        else:
            self.ns = ns
        if 'get_ipython' not in self.ns:
            # not sure if thats really needed
            self.ns['get_ipython'] = get_ipython

        self.shell = InteractiveShell.instance()        
        self.refresh()
        self.run_tag('__init__', strict=False)
        
    def restart(self):
        self.ns = dict()
        if 'get_ipython' not in self.ns:
            # not sure if thats really needed
            self.ns['get_ipython'] = get_ipython
        
    def refresh(self):
        self.cells = []
        
        with io.open(self.nb_path, 'r', encoding='utf-8') as f:
            notebook = reader.read(f)

        # convert to current notebook version
        notebook = converter.convert(notebook, current_nbformat)
        
        compiler = CachingCompiler()
        for i, cell in enumerate(notebook.cells):
            if cell.cell_type == 'code':
                # translate all magic % commands to code
                source = self.shell.input_transformer_manager.transform_cell(cell.source)
                # need to use this cell_name so it gives a nice debug information from the notebook
                cell_name = compiler.cache(source, i)
                # compile the code
                source = compile(source, cell_name, 'exec')

                self.cells.append({'code': source, 'tags': self._cell_tags(cell)})

    def _run(self, cells):
        cwd = os.getcwd()
        nb_dirname = os.path.dirname(self.nb_path)
        if nb_dirname:
            os.chdir(nb_dirname)
        for cell in cells:
            try:
                exec(cell['code'], self.ns)
            except Exception as e:
                raise e
                os.chdir(cwd)
        os.chdir(cwd)
        
    def run_all(self, blacklist=None):
        cells = self.cells[:]
        if blacklist is not None:
            if type(blacklist) == str:
                blacklist = [blacklist]
            filtered_cells = []
            for cell in cells:
                is_blacklisted = False
                for tag in blacklist:
                    if tag in cell['tags']:
                        is_blacklisted = True
                        break
                if not is_blacklisted:
                    filtered_cells.append(cell)
            cells = filtered_cells

        self._run(cells)
        return self
        
    def run_cells(self):
        raise NotImplementedError()
        
    def _cell_tags(self, cell):
        if cell.cell_type != 'code':
            return [None]
        if 'tags' not in cell.metadata:
            tags = []
        else:
            tags = cell.metadata['tags']
        if cell.source[0] == '#':
            first_line = cell.source.split('\n', 1)[0]
            first_line = first_line.strip('#').strip()
            tags += first_line.split()
        if tags == []:
            tags = [None]
        return tags

    def run_tag(self, tag, strict=True):
        cells = []
        for cell in self.cells:
            if tag in cell['tags']:
                cells.append(cell)
        if len(cells):
            self._run(cells)
        else:
            assert not strict, 'Tag "%s" found' % tag
        return self

    def __del__(self):
        self.run_tag('__del__', strict=False)
        
    def __getstate__(self):
        return (self.nb_path, self.ns)

    def __setstate__(self, d):
        self.nb_path, self.ns = d
