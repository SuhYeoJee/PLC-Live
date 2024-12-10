if __debug__:
    import sys
    sys.path.append(r"X:\Github\PLC-Live")
# -------------------------------------------------------------------------------------------
import json
from src.module.session_data import SessionData
# ===========================================================================================
DEBUG = True
# DEBUG = False
# -------------------------------------------------------------------------------------------

class state_wait():
    '''
    model의 state를 의미하는 클래스
    각 state 마다 model의 worker함수에서 읽을 dataset 정보 갖음
    특정 신호가 _is_next 조건을 만족할 때까지 반복 동작

    self.addrs : plc 전체 주소
    self.dataset : worker에서 읽을 주소
    next_state : 조건 만족시 전환되는 다음 state
    key: 조건에서 요구하는 값의 주소명
    use_tick: 주기적으로 값 읽기 여부 : bool

    _is_next : 다음 state로 넘어갈 조건 
    before_change_mode: 다음 state로 전환하기 전에 실행
    after_change_mode: 해당 state로 전환된 뒤 실행
    before_worker_tick: 틱 동작 이전 실행
    after_worker_tick: 틱 동작 이후 실행
    
    '''
    def __init__(self):
        self.addrs = self.get_plc_addrs()
        self.dataset = None
        self.next_state = None
        self.key = None
        self.use_tick = False
        
    def before_change_mode(self,**kwargs):...
    def after_change_mode(self,**kwargs):...
    def before_worker_tick(self,**kwargs):...
    def after_worker_tick(self,**kwargs):...
    def _is_next(self,val)->bool:
        '''
        state가 전환될 조건 
        @val : 새로 읽은 self.key에 대응하는 값
        '''
        ...
    # [json] -------------------------------------------------------------------------------------------
    def get_plc_addrs(self):
        '''
        json 파일 전체 읽기
        '''
        with open("./doc/PLC_ADDR.json", 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data 
    
    def get_dataset(self):
        '''
        PLC_ADDR[DATASET][STATE_NAME] 아래의 항목을 self.dataset에 등록
        PLC_ADDR[DATASET][TABLE] 아래의 항목을 self.dataset에 등록
        '''
        try:
            dataset_list = self.dataset["PLC_ADDR"]
            self.dataset.pop("PLC_ADDR")
            for i in dataset_list:
                self.dataset.update({i:self.addrs["PLC_ADDR"][i]})

            dataset_table_list = self.dataset["TABLE"]
            self.dataset.pop("TABLE")

            self.dataset["TABLE_DATAS"] = {}
            self.dataset["TABLE_ADDRS"] = {}
            for table_name in dataset_table_list:
                self.dataset["TABLE_DATAS"].update({table_name:self.addrs["TABLE_DATA"][table_name]['table']})
                self.dataset["TABLE_ADDRS"].update({table_name:self.addrs["TABLE_DATA"][table_name]['addrs']})
        except Exception as e:
            print(e)
        # print(self.dataset)

# -------------------------------------------------------------------------------------------
class start_wait(state_wait):
    def __init__(self):
        super().__init__()
        self.dataset = self.addrs["DATASET"]["START_WAIT"]
        self.get_dataset()
        self.key = "SYSTEM_RUN"
        self.use_tick = True

    def _is_next(self,val)->bool:
        '''
        조건: SYSTEM_RUN 값이 1
        '''
        if DEBUG:
            return True
        else:
            return True if val == 1 else False 
# -------------------------------------------------------------------------------------------
class exit_wait(state_wait):
    def __init__(self):
        super().__init__()
        self.dataset = self.addrs["DATASET"]["EXIT_WAIT"]                
        self.get_dataset()
        self.key = "SYSTEM_RUN"
        self.use_tick = True

    def _is_next(self,val)->bool:
        '''
        조건: SYSTEM_RUN 값이 0

        '''
        if DEBUG:
            return False
        else:
            return True if val == 0 else False 
    
    def before_change_mode(self):...
    def after_change_mode(self):
        '''
        exit_wait로 전환된 다음 실행
        SessionData 생성
        '''
        self.session = SessionData()
        self.session.data["_graph"] = [{"AUTOMATIC_SEGSIZE_1" : "DW2910"}]
        self.session.data["_alarm"] = [{"ALARM_TIME":"","ALARM_NAME":"","ALARM_STATE":""}]

    def before_worker_tick(self):...
    def after_worker_tick(self,**kwargs):
        '''새 값 기반 세션 업데이트'''
        update_data = kwargs['update_data']
        alarm_data = kwargs['alarm_data']

        if kwargs['is_graph_update']:
            self._update_sesstion_data(update_data)
            self._update_graph_data(update_data)
        self._update_alarm_data(alarm_data)
        
        '''세션 데이터 파일로 저장'''
        self.session.save_data_to_excel()

    def _update_sesstion_data(self,update_data)->None:
        '''세션데이터 - 일반 갱신'''
        for k,v in self.addrs["PLC_ADDR"].items():
            new_val = {}
            for addr_name in v.keys():
                val = update_data.get(addr_name,None)
                if val:
                    new_val[addr_name] = val
            self.session.update_data(k,new_val)

    def _update_graph_data(self, update_data) -> None:
        '''세션 데이터 - 그래프 갱신'''
        graph_val = {"AUTOMATIC_SEGSIZE_1":update_data.get("AUTOMATIC_SEGSIZE_1",None)}
        self.session.update_data("_graph", graph_val)

    def _update_alarm_data(self,alarm_data):
        '''세션 데이터 - 알람 갱신'''
        # alarm_data = {arr_label:['on',timestr]}
        new_alarm = {}
        for alarm_label,alarm_info in alarm_data.items():
            new_alarm["ALARM_TIME"] = alarm_info[1]
            new_alarm["ALARM_NAME"] = alarm_label
            new_alarm["ALARM_STATE"] = alarm_info[0]
            self.session.update_data("_alarm", new_alarm)

# -------------------------------------------------------------------------------------------
class view_wait(state_wait):
    '''
    file view 모드
    각각 생성해서 호출
    '''
    def __init__(self,file_name:str):
        super().__init__()
        self.use_tick = False
        self.session = SessionData(file_name)

# ===========================================================================================

if __name__ == "__main__":
    m = exit_wait()
    m.get_dataset()