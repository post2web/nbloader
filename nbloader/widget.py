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

from traitlets import Bool # for Output widget patch

from .notebook import Notebook





class NotebookWidget(Notebook):
    accordion_layout = w.Layout(min_width='7em', flex='1 0 8em')
    cell_output_layout = w.Layout(min_width='14em', max_height='70vh')

    _run_output = None

    def __init__(self, *a, ast_node_interactivity='last_expr', display_code=True, **kw):
        self.display_code = display_code
        super().__init__(*a, ast_node_interactivity=ast_node_interactivity, **kw)



    def show_cells(self, tag):
        if isinstance(tag, str):
            tag = (tag,)
        cells = [cell for cell in self.cells if all(t in cell['tags'] for t in tag)]
        out = Carousel()
        display(out)

        for cell in cells:
            with out.capture_item():
                display(Code(cell['source'], language='ipython3'))


    def _iter_cells(self, cells, show=True, append=False, collapsed=False):
        if append and self._run_output:
            run_output = self._run_output
        else:
            run_output = self._run_output = Carousel()

            if show:
                display(run_output)

        for cell in super()._iter_cells(cells):
            with run_output.capture_item():
                cell_output = Accordion(layout=self.accordion_layout)
                display(cell_output)

                i = self.exec_count + 1
                if self.display_code:
                    with cell_output.capture_item('In [{}]'.format(i),
                                                  layout=self.cell_output_layout):
                        display(Code(cell['source'], language='ipython3'))

                with cell_output.capture_item('Out [{}]'.format(i),
                                              selected=not collapsed,
                                              layout=self.cell_output_layout):
                    try:
                        yield cell
                    except GeneratorExit:
                        pass

'''

IPython Widget Customizations

'''

class Output(w.Output):
    stop_execution = Bool(False, help="Stop execution when exception is raised.").tag(sync=True)

    def __exit__(self, etype, evalue, tb):
        """Called upon exiting output widget context manager."""
        ip = get_ipython()

        # print(type(etype), type(evalue), hasattr(evalue, '__already_shown_by_ipywidgets_output'), evalue.__already_shown_by_ipywidgets_output)
        if etype is not None and not hasattr(evalue, '_already_shown_by_ipywidgets_output'):
            if ip:
                evalue.__already_shown_by_ipywidgets_output = True
                ip.showtraceback((etype, evalue, tb), tb_offset=0)
        self._flush()
        self.msg_id = ''
        # if self.stop_execution:
        #     raise ExceptionAlreadyShownByOutput(etype, evalue, tb)

        return not self.stop_execution if ip else None

class Carousel(w.Box):
    layout = w.Layout(
        flex_flow='row nowrap',
        overflow_x='auto',
        max_width='100%',
    )

    @contextmanager
    def capture_item(self, stop_execution=True, **kw):
        out = Output(stop_execution=stop_execution, **kw)
        self.append_item(out)
        with out:
            yield

    def append_item(self, child):
        self.children += (child,)

# TODO: add these to ipywidgets core

class Tab(w.Tab):
    @contextmanager
    def capture_item(self, title=None, selected=None, stop_execution=True, **kw):
        out = Output(stop_execution=stop_execution, **kw)
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
    def capture_item(self, title=None, selected=None, stop_execution=True, **kw):
        out = Output(stop_execution=stop_execution, **kw)
        self.append_item(out, title, selected=selected)
        with out:
            yield

    def append_item(self, child, title=None, selected=None):
        self.children += (child,)
        if title:
            self.set_title(len(self.children) - 1, title)
        if selected:
            self.selected_index = len(self.children) - 1
