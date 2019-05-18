'''


Plan:
 - Run cell - Produces


with tab.add_tab(title='hi'):
    notebook.run_tag('hi')

with tab.add_tab(title='hello'):
    notebook.run_tag('hello')

Tab 1:
 - Each cell execution is a new flexbox carousel box with accordion for: cell source & output



'''
from contextlib import contextmanager
import ipywidgets.widgets as w
from IPython.display import display, Code

from .notebook import Notebook





class NotebookWidget(Notebook):
    cell_output_layout = w.Layout(min_width='14em')
    display_code = True
    _run_output = None

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)

    def _iter_run(self, cells, show=True, append=False):
        if append and self._run_output:
            run_output = self._run_output
        else:
            run_output = self._run_output = Carousel()

            if show:
                display(run_output)

        with self._setup_environment():
            for cell in cells:
                with run_output.capture_item():
                    cell_output = Accordion()
                    display(cell_output)

                    i = self.exec_count + 1
                    if self.display_code:
                        with cell_output.capture_item('In [{}]'.format(i),
                                                      layout=self.cell_output_layout):
                            display(Code(cell['source'], language='ipython3'))

                    with cell_output.capture_item('Out [{}]'.format(i),
                                                  selected=True,
                                                  layout=self.cell_output_layout):
                        self._execute_cell(cell)
                        yield

'''

IPython Widget Customizations

'''

class Carousel(w.Box):
    layout = w.Layout(
        flex_flow='row nowrap',
        overflow_x='auto',
        max_width='100%',
    )

    @contextmanager
    def capture_item(self, **kw):
        out = w.Output(**kw)
        self.append_item(out)
        with out:
            yield

    def append_item(self, child):
        self.children += (child,)

# TODO: add these to ipywidgets core

class Tab(w.Tab):
    @contextmanager
    def capture_item(self, title=None, selected=None, **kw):
        out = w.Output(**kw)
        self.append_item(out, title, selected=selected)
        with out:
            yield

    def append_item(self, child, title=None, selected=None):
        self.children += (child,)
        if title:
            self.set_title(len(self.children) - 1, title)
        if selected:
            self.selected_index = len(self.children) - 1

class Accordion(w.Accordion):
    @contextmanager
    def capture_item(self, title=None, selected=None, **kw):
        out = w.Output(**kw)
        self.append_item(out, title, selected=selected)
        with out:
            yield

    def append_item(self, child, title=None, selected=None):
        self.children += (child,)
        if title:
            self.set_title(len(self.children) - 1, title)
        if selected:
            self.selected_index = len(self.children) - 1
