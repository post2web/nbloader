import os
import io
import pdb


from nbformat import reader, converter, current_nbformat
from IPython.core.interactiveshell import InteractiveShell
from IPython import get_ipython
from IPython.core.compilerop import CachingCompiler

class Notebook(object):
    
    def __init__(self, nb_path, ns={}):
        self.nb_path = nb_path
        self.ns = ns
        if 'get_ipython' not in ns:
            # not sure if thats really needed
            ns['get_ipython'] = get_ipython

        self.shell = InteractiveShell.instance()        
        self.refresh()
        self.run('__init__', strict=False)

    def refresh(self):
        with io.open(self.nb_path, 'r', encoding='utf-8') as f:
            notebook = reader.read(f)
        # convert to current notebook version
        notebook = converter.convert(notebook, current_nbformat)
        
        compiler = CachingCompiler()
        self.nb_cells = {}
        for i, cell in enumerate(notebook.cells):
            code = cell.source
            if not len(code) or cell.cell_type != 'code':
                continue
            if code[:2] == '#@':
                cell_header = code.split('\n', 1)[0].lstrip("#@").rstrip()
            else:
                cell_header = None
            if cell_header not in self.nb_cells:
                self.nb_cells[cell_header] = []
            # translate all magic % commands to code
            code = self.shell.input_transformer_manager.transform_cell(code)
            # need to use this cell_name so it gives a nice debug information from the notebook
            cell_name = compiler.cache(code, i)
            # compile the code
            code = compile(code, cell_name, 'exec')
            self.nb_cells[cell_header].append(code)

    def _run(self, cells):
        cwd = os.getcwd()
        nb_dirname = os.path.dirname(self.nb_path)
        if nb_dirname: os.chdir(nb_dirname)
        for cell in cells:
            exec(cell, self.ns)
        os.chdir(cwd)

    def run_all(self):
        self._run(self.nb_cells)
        return self
    
    def run(self, cell_header=None, strict=True):
        if strict:
            assert cell_header in self.nb_cells.keys()
            cells = self.nb_cells[cell_header]
        else:
            if cell_header in self.nb_cells:
                cells = self.nb_cells['cell_header']
            else:
                cells = []
        self._run(cells)
        return self
        
    def __del__(self):
        self.run('__del__', strict=False)
        
    def __getitem__(self, key):
        return self.ns[key]

    def __setitem__(self, key, value):
        self.ns[key] = value

    def __delitem__(self, key):
        del self.ns[key]

    def __contains__(self, key):
        return key in self.ns

    def __getattr__(self, key):
        if key.startswith('__') and key.endswith('__'):
            return super(Notebook, self).__getattr__(key)
        def _missing(*args, **kwargs):
            assert not args, 'Only key arguments are allowed!'
            self.ns.update(kwargs)
            return self.run(key)
        return _missing
        
    def __getstate__(self):
        return (self.nb_path, self.ns)

    def __setstate__(self, d):
        self.nb_path, self.ns = d
        