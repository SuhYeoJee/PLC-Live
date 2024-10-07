if __debug__:
    import sys
    sys.path.append(r"X:\Github\PLC-Live")
# -------------------------------------------------------------------------------------------
import json
from src.module.session_data import sessionData
# ===========================================================================================

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
        with open("./src/spec/PLC_ADDR.json", 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data 
    
    def get_dataset(self):
        '''
        PLC_ADDR[DATASET][STATE_NAME] 아래의 항목을 self.dataset에 등록
        '''
        try:
            dataset_list = self.dataset["PLC_ADDR"]
            self.dataset.pop("PLC_ADDR")
            for i in dataset_list:
                self.dataset.update(self.addrs["PLC_ADDR"][i])
        except Exception as e:
            print(e)
            ...
        # print(self.dataset)


# -------------------------------------------------------------------------------------------
class connect_wait(state_wait):
    def __init__(self):
        super().__init__()
        self.dataset = self.addrs["DATASET"]["CONNECT_WAIT"]
        self.get_dataset()
        self.key = "SYSTEM_RUN"
        self.use_tick = False

    def _is_next(self,val)->bool:
        '''
        조건: 값이 정상적으로 읽어짐 (내용과 상관 없음)
        '''
        if val == None: # 연결실패
            self.use_tick = False
            print("PLC 연결 실패") #알림 띄워야함
            return False
        else:
            return True # 연결 성공, 시작대기로 전환
        
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
        return True if val == '1' else False
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
        return True if val == '0' else False
    
    def before_change_mode(self):...
    def after_change_mode(self):
        '''
        exit_wait로 전환된 다음 실행
        sessionData 생성
        '''
        self.session = sessionData()
        self.session.data["graph"] = [{"AUTOMATIC_SEGSIZE_1" : "DW2910"}]

    def before_worker_tick(self):...
    def after_worker_tick(self,**kwargs):
        '''
        worker_tick 실행된 다음 실행
        _save_excel: sessionData 갱신, 저장
        '''
        update_data = kwargs['update_data']
        self._save_excel(update_data)

    def _save_excel(self,update_data):
        graph_val = {}
        for k,v in self.addrs["PLC_ADDR"].items():
            new_val = {}
            for addr_name in v.keys():
                val = update_data.get(addr_name,None)
                if val:
                    new_val[addr_name] = val
                if addr_name in ["AUTOMATIC_SEGSIZE_1"]:
                    graph_val[addr_name] = val
            self.session.update_data(k,new_val)
        self.session.update_data("graph",graph_val)
        
        self.session.save_data_to_excel()

# -------------------------------------------------------------------------------------------
class view_wait(state_wait):
    '''
    file view 모드
    각각 생성해서 호출
    '''
    def __init__(self,file_name:str):
        super().__init__()
        self.use_tick = False
        self.session = sessionData(file_name)

# ===========================================================================================

if __name__ == "__main__":
    m = exit_wait()
    m.get_dataset()