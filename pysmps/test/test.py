import unittest
import math

import os,sys,inspect
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir) 
from mps_loader import read_mps

class TestMPSReader(unittest.TestCase):
        
    def test_case01(self):
        self.maxDiff=None
        self.assertDictEqual(
            dict(read_mps(current_dir + "/case01")),
            {'name': 'test_case01',
            'objective_names': ['obj'],
            'objectives': {
                'obj':
                    {'coefficients': {
                        'c_bnd': 1.5,
                        'c_bnd2': 2.5,
                        'c_bnd3': -3.5,
                        'c_bnd_up': -4.5,
                        'c_bnd_lo': 5.5,
                        'int': 9.0,
                        'bin': 9.5,
                        'free': -120.5,
                        'fixed': 120.5
                    }
                }
            },
            'bnd_names': ['BND'],
            'rhs_names': ['RHS'],
            'variables': {
                'BND': {
                    'c_bnd': {
                        'type': 'Continuous',
                        'lower': -5.0,
                        'upper': 10.0
                    },
                    'c_bnd2': {
                        'type': 'Continuous',
                        'lower': 5.0,
                        'upper': 100.0
                    },
                    'c_bnd3': {
                        'type': 'Continuous',
                        'lower': -100.0,
                        'upper': -5.0
                    },
                    'c_bnd_up': {
                        'type': 'Continuous',
                        'lower': 0.0,
                        'upper': 10.0
                    },
                    'c_bnd_lo': {
                        'type': 'Continuous',
                        'lower': -10.0,
                        'upper': math.inf
                    },
                    'int': {
                        'type': 'Integer',
                        'lower': 5.0,
                        'upper': 10.0
                    },
                    'bin': {
                        'type': 'Integer',
                        'lower': 0.0,
                        'upper': 1.0
                    },
                    'free': {
                        'type': 'Continuous',
                        'lower': -math.inf,
                        'upper': math.inf
                    },
                    'fixed': {
                        'type': 'Continuous',
                        'lower': 20.5,
                        'upper': 20.5
                    }
                }
            },
            'constraint_names': ['leq', 'eq', 'geq'],
            'constraints': {
                'leq': {
                    'type': 'L',
                    'coefficients': {'c_bnd': 5.0, 'c_bnd3': -10.0, 'c_bnd_up': -1.0, 'c_bnd_lo': 1.0, 'int': 1.5, 'bin': 150.0}
                },
                'eq': {
                    'type': 'E',
                    'coefficients': {'c_bnd': 21.0, 'c_bnd2': -10.0, 'c_bnd_lo': 3.0, 'int': 2.5}
                },
                'geq': {
                    'type': 'G',
                    'coefficients': {'c_bnd': 18.0, 'c_bnd_up': -5.0, 'int': -3.5, 'free': 250.0}
                }
            },
            'rhs': {
                'RHS': {
                    'leq': -50.0,
                    'eq': 100.0,
                    'geq': -85.0
                }
            },
            'offsets': {'RHS': {'obj': 0}}
        })
        
    def test_case02(self):
        self.assertDictEqual(
            read_mps(current_dir + "/case02"),
            {'objective': {
                'name': 'obj',
                'coefficients': [
                    {'name': 'c_bnd', 'value': 1.5},
                    {'name': 'c_bnd2', 'value': 2.5},
                    {'name': 'c_bnd3', 'value': -3.5},
                    {'name': 'c_bnd_up', 'value': -4.5},
                    {'name': 'c_bnd_lo', 'value': 5.5},
                    {'name': 'int', 'value': 9.0},
                    {'name': 'bin', 'value': 9.5},
                    {'name': 'free', 'value': -120.5},
                    {'name': 'fixed', 'value': 120.5}
                ]
            },
            'variables': {
                'c_bnd': {
                    'type': 'Continuous',
                    'name': 'c_bnd',
                    'bnd_lower': -5.0,
                    'bnd_upper': 10.0
                },
                'c_bnd2': {
                    'type': 'Continuous',
                    'name': 'c_bnd2',
                    'bnd_lower': 5.0,
                    'bnd_upper': 100.0
                },
                'c_bnd3': {
                    'type': 'Continuous',
                    'name': 'c_bnd3',
                    'bnd_lower': -100.0,
                    'bnd_upper': -5.0
                },
                'c_bnd_up': {
                    'type': 'Continuous',
                    'name': 'c_bnd_up',
                    'bnd_lower': 0,
                    'bnd_upper': 5.0
                },
                'c_bnd_lo': {
                    'type': 'Continuous',
                    'name': 'c_bnd_lo',
                    'bnd_lower': -5.0,
                    'bnd_upper': math.inf
                },
                'int': {
                    'type': 'Integer',
                    'name': 'int',
                    'bnd_lower': 5.0,
                    'bnd_upper': 10.0
                },
                'bin': {
                    'type': 'Integer',
                    'name': 'bin',
                    'bnd_lower': 0.0,
                    'bnd_upper': 1.0
                },
                'free': {
                    'type': 'Continuous',
                    'name': 'free',
                    'bnd_lower': -math.inf,
                    'bnd_upper': math.inf
                },
                'fixed': {
                    'type': 'Continuous',
                    'name': 'fixed',
                    'bnd_lower': 20.5,
                    'bnd_upper': 20.5
                }
            },
            'constraints': {
                'leq': {
                    'type': 'L',
                    'name': 'leq',
                    'coefficients': [{'name': 'c_bnd', 'value': 5.0}, {'name': 'c_bnd3', 'value': -10.0}, {'name': 'c_bnd_up', 'value': -1.0}, {'name': 'c_bnd_lo', 'value': 1.0}, {'name': 'int', 'value': 1.5}, {'name': 'bin', 'value': 150.0}],
                    'bounds': {'RHS1': -50.0, 'RHS2': 50.0}
                }
            },
            'rhs_names': ['RHS1', 'RHS2']
        })
        
class TestMPSWriter(unittest.TestCase):
    
    def test_case01(self):
        return
    
if __name__ == '__main__':
    unittest.main()