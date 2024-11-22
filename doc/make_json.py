if __debug__:
    import sys
    sys.path.append(r"X:\Github\PLC-Live")
from src.module.config_manager import ConfigManager
import pprint

cm = ConfigManager('./doc/addrs.txt')

def get_addr_with_option(key)->str:
    '''config key값으로 옵션생성'''
    addr,size,datatype,exponent = key.split(',')
    size = int(size)
    exponent = int(exponent)

    if datatype == 'S':
        value_type = datatype
    elif exponent >= 0: # int
        value_type = 'i' if 'U' in datatype else 'I'
    else: #exponent < 0 # float
        value_type = 'f' if 'U' in datatype else 'F'

    res = f'%{addr}#{size:02}{value_type}{abs(exponent):02}'
    return res

def get_plc_addr_section()->dict:
    '''PLC_ADDR 섹션 반환'''
    res = {"PLC_ADDR":{}}
    for section_name in ["AUTOMATIC","PROGRAM","PROGRAM_LIST","PROGRAM_VIEW","ALARM","SYSTEM"]:
        res["PLC_ADDR"][section_name] = {}
        for key,val in cm.get_section_items(section_name).items():
            res["PLC_ADDR"][section_name][val] = get_addr_with_option(key)
    return res

def get_table_data_section()->dict:
    # 테이블 룰 복기
    res = {"table_data":{}}
    for key,val in cm.get_section_items('TABLE').items():
        res["table_data"][key] = val
    return res

if __name__ == "__main__":
    pprint.pprint(get_table_data_section())