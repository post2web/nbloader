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

    def refresh(self):
        self._cells = []
        compiler = CachingCompiler()
        
        with io.open(self.nb_path, 'r', encoding='utf-8') as f:
            notebook = reader.read(f)
        # convert to current notebook version
        notebook = converter.convert(notebook, current_nbformat)
        
        self._notebook = notebook

        # compile
        for i, cell in enumerate(notebook.cells):
            if cell.cell_type == 'code':
                # translate all magic % commands to code
                source = self.shell.input_transformer_manager.transform_cell(cell.source)
                # need to use this cell_name so it gives a nice debug information from the notebook
                cell_name = compiler.cache(source, i)
                # compile the code
                cell.source = compile(source, cell_name, 'exec')

    def _run(self, cells):
        cwd = os.getcwd()
        nb_dirname = os.path.dirname(self.nb_path)
        if nb_dirname: os.chdir(nb_dirname)
        for cell in cells:
            if cell.cell_type != 'code':
                continue
            try:
                exec(cell.source, self.ns)
            except Exception as e:
                raise e
                os.chdir(cwd)
        os.chdir(cwd)
        
    def run_all(self):
        self._run(self._notebook.cells)
        return self
        
    def run_cells(self):
        raise NotImplementedError() 

    def run_tag(self, tag, strict=True):
        cells = []
        for cell in self._notebook.cells:
            if 'tags' not in cell.metadata:
                tags = [None]
            else:
                tags = cell.metadata['tags']
            if tag in tags:
                cells.append(cell)

        if len(cells):
            self._run(cells)
        else:
            assert not strict, 'Tag "%s" found' % tag
            

        return self
        
    #
    #
    # The following methods to act more as a regular object
    #
    #

    def __del__(self):
        self.run_tag('__del__', strict=False)
        
    def __getstate__(self):
        return (self.nb_path, self.ns)

    def __setstate__(self, d):
        self.nb_path, self.ns = d


    # def __getitem__(self, key):
    #     return self.ns[key]
    #
    # def __setitem__(self, key, value):
    #     self.ns[key] = value
    #
    # def __delitem__(self, key):
    #     del self.ns[key]
    #
    # def __contains__(self, key):
    #     return key in self.ns
    #
    # def __getattr__(self, key):
    #     if key.startswith('__') and key.endswith('__'):
    #         return super(Notebook, self).__getattr__(key)
    #     def _missing(*args, **kwargs):
    #         assert not args, 'Only key arguments are allowed!' + str(args)
    #         self.ns.update(kwargs)
    #         return self.run(key)
    #     return _missing
    #
