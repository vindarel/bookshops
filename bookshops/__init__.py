import os
import sys

# Add "datasources" to sys.path 
# so than we can "import bookshops"
common_dir = os.path.dirname(os.path.abspath(__file__))
cdp, _ = os.path.split(common_dir)
sys.path.append(cdp)
