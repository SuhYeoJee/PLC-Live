if __debug__:
    import sys
    sys.path.append(r"X:\Github\PLC-Live")
from src.module.config_manager import ConfigManager
import pprint
import json


TEXT_PATH = './doc/addrs.txt'
JSON_PATH = './doc/PLC_ADDR.json'

cm = ConfigManager(TEXT_PATH)

def get_addr_with_option(key)->str:
    '''config key값으로 옵션생성'''
    addr,size,datatype,exponent = key.split(',')
    size = int(size)
    exponent = int(exponent)

    if datatype == 'S': #string
        value_type = datatype
    elif datatype == 'X': #bit
        value_type = datatype
    elif datatype == 'A': # alarm(A: 1=on) (a: 0=on)
        value_type = 'a' if exponent == 0 else 'A'
    elif exponent >= 0: # int (I: usigned) (i: signed)
        value_type = 'I' if 'U' in datatype else 'i'
    else: #exponent < 0 # float (F: usigned) (f: signed)
        value_type = 'F' if 'U' in datatype else 'f'

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
    '''TABLE_DATA 섹션 반환'''
    res = {"TABLE_DATA":{}}
    for table_info,table_name in cm.get_section_items('TABLE_HEAD').items():
        table_start_addr,table_size = table_info.split(',')
        table_size = int(table_size)
        new_dict = {}
        for key,val in cm.get_section_items(table_name).items():
            new_dict[val] = get_addr_with_option(key)
        res["TABLE_DATA"][table_name] = {"table" :{"addrs":list(new_dict.values()), "start_addr":table_start_addr, "size":table_size},"addrs":new_dict}
    return res

def get_dataset_section()->dict:
    '''DATASET 섹션 반환'''
    table_sections = list(cm.get_section_items("TABLE_HEAD").values())
    res = {
        "DATASET":{
        "START_WAIT":{
            "PLC_ADDR":["SYSTEM","ALARM"]
        },
        "EXIT_WAIT":{
            "PLC_ADDR":["AUTOMATIC","PROGRAM","PROGRAM_LIST","PROGRAM_VIEW","ALARM","SYSTEM"],
            "TABLE":table_sections
        }
    }}
    return res


def get_json()->dict:
    res = get_plc_addr_section()
    res.update(get_table_data_section())
    res.update(get_dataset_section())
    with open(JSON_PATH, "w") as json_file:
        json.dump(res, json_file, indent=4)
    return res

if __name__ == "__main__":
    get_json()