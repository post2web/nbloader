# nbloader

nbloader contains a set of tools designed to help you reuse code from Jupyter notebook cells. Tested to work with python 2.7

To install/upgrade:
>pip install git+git://github.com/post2web/nbloader.git@master --upgrade

To create reusable code in a notebook
    
- write the reusable code in a notebook cell
- create a cell header with a name identifier
    - the header is always on the fist row of the cell
    - starts with #@ and a name identifier
    - name identifier should be a valid function name

Example: Jupyter notebook test.ipynb has one cell:
```sh
#@my_header_name
print 'test'
```
To reuse this cell in a different notebook in same directory:
```sh
from nbloader import Notebook
nb = Notebook('test.ipynb')
# every header name in test.ipynb becomes a method in Notebook
nb.my_header_name() # prints test
```
The Notebook class keeps his own namespace but you can interact with it.

In example.ipynb
```sh
#@calculate
a = b * c
```

In main.ipynb
```sh
nb = Notebook('example.ipynb')
nb.calculate()
# this will give you "NameError: name 'b' is not defined"
# because b is not set in the namespace of the notebook
# to send variables into the namespace use named arguments
nb.calculate(b=5, c=2)
# to get variable "c" from the notebook's namespace
a = nb['a']
# since "b" and "c" are already set into the nb's namespace
# this will now execute without an exception:
nb.calculate()
# you can push/pull variables as you would with a dict
nb['c'] = 10
nb['b'] = 2
nb.calculate()
assert nb['a'] == 10
```

There are situations where you want to stop execution with return like notation. Raise nbloader.Exit for that.

```sh
#@exec
from nbloader import Exit
if True:
	raise Exit
print 'I am in cell 1' 
```
Then you could have a second cell with the same name:
```sh
#@exec
print 'I am in cell 2'
```

In main.ipynb
```sh
Notebook('example.ipynb').exec()
# nothing will be printed.
```


Other useful features:
- multiple cells could have the same header name.
- header named \_\_init\_\_ will be executed when instance of Notebook class is created
- header named \_\_del\_\_ will be executed when instance of Notebook class is deleted
- handles magic commands
- executed notebook can change working directory without affecting parent notebook
- uses relative ( ../../test.ipynb ) or full paths ( /users/notebooks/test.ipynb ) 
- uses the same process so nothing is been pickled when you pass variables
- all code is completed so Notebook methods can be called in a loop without any overhead

Best practices coming soon!
