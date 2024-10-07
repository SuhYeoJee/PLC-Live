if __debug__:
    import sys
    sys.path.append(r"X:\Github\PLC-Live")
# -------------------------------------------------------------------------------------------
from src.module.plcl_utils import get_now_str
import pandas as pd
from os import path, makedirs, remove
import shutil
import json
# ===========================================================================================

'''
    수정불필요
'''

class SessionData:
    def __init__(self,file_name:str=None):
        if file_name: #load data
            self.file_name = file_name
            self.read_data_from_excel(file_name)
            self.is_new:bool = False
        else: #new data
            self.file_name = get_now_str("./result/%Y-%m-%d_%H-%M-%S.xlsx")
            self.is_new:bool = True
            # 엑셀 형식 {시트명:[{열이름:값,}]} #갱신시 새 딕셔너리를 리스트에 추가
            self.data = self.get_data_form()

    # --------------------------
    def get_data_form(self):
        '''
        json.PLC_ADDR 항목 자동으로 읽어옴
        DATASET 이름을 시트명으로, 주소명을 열제목으로 사용
        '''
        with open("./src/spec/PLC_ADDR.json", 'r', encoding='utf-8') as file:
            data = json.load(file)
        return {k:[v] for k,v in data["PLC_ADDR"].items()}
    # -------------------------------------------------------------------------------------------
    def update_data(self,sheet_name:str,data:dict)->None:
        '''
        최신값 기록
        sheet_name에 상응하는 리스트의 끝에 data 추가
        '''
        update_target = self.data.get(sheet_name,False)
        if not update_target:
            self.data[sheet_name] = []
            
        new_value = {k:v for k,v in self.data[sheet_name][-1].items()}
        new_value.update(data)
        update_target.append(new_value)
    # --------------------------
    def save_data_to_excel(self):
        '''
        sessionData를 엑셀로 저장 (초기 빈값 제외)
        '''
        temp_file_name = "temp.xlsx"
        try:
            if not path.exists('result'): makedirs('result')
            with pd.ExcelWriter(temp_file_name) as writer:
                for sheet_name, sheet_data in self.data.items():
                    df = pd.DataFrame(sheet_data[1:])
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
            shutil.copy(temp_file_name, self.file_name)
        finally:
            if path.exists(temp_file_name):
                remove(temp_file_name)
    # --------------------------
    def read_data_from_excel(self,file_name):
        '''
        엑셀 값을 self.data형식에 맞게 읽기 
        '''
        if not path.exists(file_name):
            print(f"no file: {file_name}")
            return
        else:
            self.file_name = file_name

        excel_data = {}
        try:
            xls = pd.ExcelFile(file_name)
            for sheet_name in xls.sheet_names:
                df = pd.read_excel(file_name, sheet_name=sheet_name)
                excel_data[sheet_name] = df.to_dict(orient='records')
        except Exception as e:
            print("file read error:", str(e))

        self.data = excel_data
        return excel_data
    
# ===========================================================================================
if __name__=="__main__":
    s = SessionData()
    print(s.data)
    s.update_data("AUTOMATIC",{"AUTOMATIC_PRGNO":"13","AUTOMATIC_PRGNAME":""})
    print(s.data)
    s.save_data_to_excel()
