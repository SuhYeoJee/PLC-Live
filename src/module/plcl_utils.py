if __debug__:
    import sys
    sys.path.append(r"X:\Github\PLC-Live")
# -------------------------------------------------------------------------------------------
from datetime import datetime
# ===========================================================================================

def get_now_str(format:str = "%Y-%m-%d %H:%M:%S")->str:
    now_str = datetime.now().strftime(format.encode('unicode-escape').decode()).encode().decode('unicode-escape')

    return now_str