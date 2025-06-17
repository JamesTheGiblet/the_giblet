# This function has a bug
def add(a, b):
    if not isinstance(a,(int,float)) or not isinstance(b,(int,float)):
        raise TypeError("Inputs must be numbers")
    return a + b