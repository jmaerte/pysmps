# smps_py_parser
Utility for parsing smps files.
## Installation
Clone this repository and execute
```bash
pip install -e .
```
inside the cloned folder. This should install the module *smpspy* to your pip list. You can then import this module using
```python
from smpspy import smps_loader as smps
```
at the beginning of your python code.
You maybe want the folder you cloned to be in your PYTHONPATH, so check that if it is not working.
## Functions
This module exports the functions `load_lp` for loading mps files and `load_smps` for loading smps directories.
## TODO
- [ ] Scenario support in sto file parsing.
- [ ] Block support in 2-stage problem casting.
