import sys
import os

# hack the Python path so jToolkit can import itself... yucky
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))
