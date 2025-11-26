import sys
import io
import contextlib
import traceback
import math
import fractions
import itertools
import sympy
import numpy

def execute_python_code(code:str) -> (str,str,str):
    """
    Execute python code in a safe environment.

    Args:
        code (str): The python code to execute.
        
    Returns:
        tuple(stdout, stderr, return_value): 
        - stdout: The standard output captured from execution.
        - stderr: Error messages if execution failed.
        - return_value: A string representation of the final result (if any).
    """
    
    # 1. Prepare execution environment
    exec_globals = {
        "math": math,
        "fractions": fractions,
        "itertools": itertools,
        "sympy": sympy,
        "numpy": numpy,
        "__builtins__": {
            "print": print,
            "range": range,
            "len": len,
            "int": int,
            "float": float,
            "str": str,
            "list": list,
            "dict": dict,
            "set": set,
            "tuple": tuple,
            "bool": bool,
            "abs": abs,
            "min": min,
            "max": max,
            "sum": sum,
            "enumerate": enumerate,
            "zip": zip,
            "map": map,
            "filter": filter,
            "sorted": sorted,
            "reversed": reversed,
            "__import__": __import__,
        }
    }

    # 2. Capture stdout and stderr
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()
    
    return_val = ""

    try:
        # 3. Execute the code
        with contextlib.redirect_stdout(stdout_capture),contextlib.redirect_stderr(stderr_capture):
            exec_locals = {}
            exec(code, exec_globals, exec_locals)

            # Return value
            if 'result' in exec_locals:
                return_val = str(exec_locals['result'])

    except Exception:
        # 4. Handle errors
        traceback.print_exc(file=stderr_capture)

    # 5. Get strings
    stdout_str = stdout_capture.getvalue()
    stderr_str = stderr_capture.getvalue()

    # Close buffers
    stdout_capture.close()
    stderr_capture.close()

    return stdout_str, stderr_str, return_val

