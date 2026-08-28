#!/usr/bin/env python3
"""
Testing script for market recorder to help verify correct operation.
This can be used if the direct module run fails.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from app.tools.market_recorder import main
    print("Market recorder imported successfully")
    print("Running with main() function directly")
    exit_code = main()
    sys.exit(exit_code)
except Exception as e:
    print(f"Error running market recorder: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)