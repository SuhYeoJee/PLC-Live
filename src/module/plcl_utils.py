if __debug__:
    import sys
    sys.path.append(r"X:\Github\PLC-Live")
# -------------------------------------------------------------------------------------------
from datetime import datetime
# ===========================================================================================

def get_now_str(format:str = "%Y-%m-%d %H:%M:%S")->str:
    now_str = datetime.now().strftime(format.encode('unicode-escape').decode()).encode().decode('unicode-escape')

    return now_str

def is_float_str(target:str)->bool:
    try:
        float(target)
        return True
    except:
        return False
    
def get_sort_vals_by_key(input:dict)->list:
    '''딕셔너리 key의 마지막 숫자 오름차순으로 정렬된 val리스트 반환'''
    sorted_items = sorted(input.items(), key=lambda item: int(item[0].split('-')[-1]))
    return [val for _, val in sorted_items]