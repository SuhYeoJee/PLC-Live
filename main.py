if __debug__:
    import sys
    sys.path.append(r"X:\Github\PLC-Live")
# -------------------------------------------------------------------------------------------
from src.controller import main

if __name__ == "__main__":
    print("PRESS MONITOR: G1.3")
    main()
