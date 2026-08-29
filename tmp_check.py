import py_compile
from pathlib import Path


py_compile.compile(str(Path(__file__).with_name('mng.py')), doraise=True)
print('py_compile_ok')
