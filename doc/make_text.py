if __debug__:
    import sys
    sys.path.append(r"X:\Github\PLC-Live")
# -------------------------------------------------------------------------------------------
from src.module.config_manager import ConfigManager
# -------------------------------------------------------------------------------------------

def make_program_addrs(table_head:str="%DW5080,270",table_name:str="PROGRAM_VIEW_TABLE-1")->dict:
    start_addr,_ = table_head.split(',')
    table_label = table_name.split('-')[0].strip()
    addr = int(start_addr.strip()[3:-1]) # 508

    prg_lines = {}
    prg_lines[f"DW{addr}0,1,16U,0"] = f"{table_label}_USE_STEP"
    prg_lines[f"DW{addr}1,1,16S,-2"] = f"{table_label}_PRESS_SIZE"
    prg_lines[f"DW{addr}2,1,16S,-1"] = f"{table_label}_PRESSING_TIME"

    for i in range(1,11):
        prg_line_addr = (addr+2) + (i - 1) # 510, 511, 512,,, 
        prg_lines[f"# {prg_line_addr}"] = "----------------------------------------------------------"
        # --------------------------
        prg_lines[f"DW{prg_line_addr}0,1,16U,-2"] = f"{table_label}_PRG{i}_STEPDIMENSION"
        prg_lines[f"DW{prg_line_addr}1,1,16U,-2"] = f"{table_label}_PRG{i}_COMPENSATE_DIMENSION"
        prg_lines[f"DW{prg_line_addr}2,1,16U,-2"] = f"{table_label}_PRG{i}_CHARGEDIMENSION"
        prg_lines[f"DW{prg_line_addr}3,1,16U,-1"] = f"{table_label}_PRG{i}_FWDTIME"
        prg_lines[f"DW{prg_line_addr}4,1,16U, 0"] = f"{table_label}_PRG{i}_SELECT_CAR"
        prg_lines[f"DW{prg_line_addr}5,1,16U, 0"] = f"{table_label}_PRG{i}_OSCCOUNT"
        prg_lines[f"DW{prg_line_addr}6,1,16U,-1"] = f"{table_label}_PRG{i}_BWDTIME"
        prg_lines[f"DW{prg_line_addr}7,1,16S,-2"] = f"{table_label}_PRG{i}_PRESSPOSITION"
        prg_lines[f"DW{prg_line_addr}8,1,16U, 1"] = f"{table_label}_PRG{i}_FINALPRESSURE"
        prg_lines[f"DW{prg_line_addr}9,1,16U, 0"] = f"{table_label}_PRG{i}_COMPENSATE_SELECT"

    return prg_lines    


if __name__ == '__main__':
    cm = ConfigManager('./doc/temp.txt')
    table_heads = cm.get_section_items("TABLE_HEAD")

    for k,v in table_heads.items():
        prg_lines = make_program_addrs(k,v)
        cm.new_section(v)
        cm.new_item(v,prg_lines)

    # print(cm.get_section_keys("PROGRAM_TABLE"))
    