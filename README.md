# nbloader: Load Jupyter Notebooks as python objects
## Useful for reusing code from Jupyter Notebooks

To install/upgrade:
>pip install git+git://github.com/post2web/nbloader.git@master --upgrade

To run all cells from a notebook [test_notebook.ipynb](tests/test_notebook.ipynb):
```sh
from nbloader import Notebook
notebook = Notebook('test_notebook.ipynb')
notebook.run_all()
print(notebook.ns['b']) # prints out 10
```
The Notebook object has its own name space: notebook.ns


You can run individual cells using cell tags. 
Show cell tags with "View/Cell Toolbar/Tags"
![show tags](show_tags.png)


To run a cell with tag add_one:
```sh
from nbloader import Notebook
notebook = Notebook('test_notebook.ipynb')
notebook.run_tag('add_one')
print(notebook.ns['a']) # 6
notebook.run_tag('add_one')
print(notebook.ns['a']) # 7
notebook.ns['a'] = 0
notebook.run_tag('add_one')
print(notebook.ns['a']) # 1
```


The notebook variable is just a python object that holds the code of the Jupyter Notebook within its name space. It uses the same process as the main program so there is no need of a jupyter server, you can pass large variables to the notebook.ns and call cells in a loop without an overhead.


Other useful features:
- notebooks can be executed within global name space 
``` notebook = Notebook('test.ipynb', ns=globals()) ```
- the notebooks can be pickled
- multiple cells could have the same tag name.
- cells taged with \_\_init\_\_ will be executed when instance of Notebook class is created
- cells taged with  \_\_del\_\_ will be executed when instance of Notebook class is deleted
- handles magic commands
- executed notebook can change working directory without affecting parent notebook
- uses relative ( ../../test.ipynb ) or full paths ( /users/notebooks/test.ipynb ) 

Best practices coming soon!