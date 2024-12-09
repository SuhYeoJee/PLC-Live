if __debug__:
    import sys
    sys.path.append(r"X:\Github\PLC-Live")
# -------------------------------------------------------------------------------------------
from src.LS_PLC import LS_plc
from src.module.plcl_utils import get_now_str
from src.state import connect_wait, start_wait, exit_wait
# --------------------------
# from igzg.utils import get_config
# ===========================================================================================
class Model():
    '''
    worker_tick: plc 데이터 읽기, is_next 조건 확인 : 주기적으로 실행
    '''
    def __init__(self):
        self.plc = LS_plc('192.168.0.50')
        self._init_state()
        # self.alarms = {} # {label:'on', label:'off'}
        self.graph_value = None

    def _init_state(self)->None:
        self.c_w = connect_wait()
        self.s_w = start_wait()
        self.e_w = exit_wait()
        self.v_w = None # view mod
        self.c_w.next_state = self.s_w
        self.s_w.next_state = self.e_w
        self.e_w.next_state = self.s_w
        # --------------------------
        self.state = self.c_w # 초기상태 
        # --------------------------
        self.alarms = {k:'off' for k in self.state.addrs["PLC_ADDR"]["ALARM"].keys()}

    # [PLC] -------------------------------------------------------------------------------------------
    def _get_update_data(self)->dict:
        result = {}
        for section_name, section_data in self.state.dataset.items():
            new_datas = {}
            if section_name == "TABLE_ADDRS":
                ...
            elif section_name == "TABLE_DATAS":
                for table_name,table_data in section_data.items():
                    new_datas.update(self.plc.read(table = table_data))
                    result.update({label: new_datas[base] for label, addr in self.state.dataset["TABLE_ADDRS"][table_name].items() if (base := addr.split('#')[0]) in new_datas})
            else:
                new_datas.update(self.plc.read(single=list(section_data.values())))
                result.update({label: new_datas[base] for label, addr in section_data.items() if (base := addr.split('#')[0]) in new_datas})
        return result

    # ==============================
    def _change_mode(self)->None:
        self.state.before_change_mode()
        self.state = self.state.next_state
        print(f'_change_mode:{type(self.state).__name__}')
        self.state.after_change_mode()

    def worker_tick(self)->list:
        '''
        1. PLC 데이터 갱신
        2. state 전환
        update_data,alarm_data,is_graph_update
        '''
        try:
            self.state.before_worker_tick()

            update_data = self._get_update_data() # plc 데이터 읽기
            alarm_data = self._update_alarm(update_data)
            is_graph_update = self._update_graph(update_data)

            is_next = self.state._is_next(update_data[self.state.key]) # 읽은 항목에서 state체크
            if is_next: # state 넘어가기
                self._change_mode()
                if self.state == self.e_w: #임시 알람 초기화
                    self.alarms = {k:'off' for k in self.state.addrs["PLC_ADDR"]["ALARM"].keys()}

            self.state.after_worker_tick(update_data=update_data)

            return [update_data,alarm_data,is_graph_update]
        except:
            print('model.worker_tick error')
            return [{},{},False]

    def _update_alarm(self,update_data:dict)->dict:
        result = {}
        if not (alarms:={k:v for k,v in update_data.items() if 'ALARM' in k}):
            return result

        # 기존 상태와 비교
        for label,value in alarms.items():
            alarm_state = self._alarm_check(label,value)
            try:
                if alarm_state != self.alarms[label]:
                    result[label] = [alarm_state,get_now_str()]
                    self.alarms[label] = alarm_state # update
                else:
                    ...
            except KeyError:
                result[label] = [alarm_state,get_now_str()]

        return result #{arr_label:['on',timestr]}

    def _alarm_check(self,label,value):
        try:
            alarm_addr = self.state.dataset['ALARM'][label]
            plc_addr,_,option = alarm_addr.partition('#')
            if option[2] == 'A': #(1=on)
                return 'on' if value == 1 else 'off'
            elif option[2] == 'a': #(0=on)
                return 'on' if value == 0 else 'off'
            else:
                raise(f'alarm_addr_option_err:{alarm_addr}')
        except Exception as e:
            print(e)
        

    def _update_graph(self,update_data)->bool:
        if 'AUTOMATIC_ACTUAL_WORKCOUNT' not in update_data.keys():
            return False
        
        # 그래프 갱신 판단
        graph_value = update_data['AUTOMATIC_ACTUAL_WORKCOUNT']
        if graph_value != self.graph_value:
            self.graph_value = graph_value
            return True
        
        return False 


# ===========================================================================================
if __name__ == "__main__":
    m = Model()
    # m._get_update_data()
    ## json test
    # print(m.state.addrs["PLC_ADDR"]["AUTOMATIC"]["PRGNO"])
    ## ADDR PASING
    # print(m.plc.get_plc_data('DW100'))
    # print(m.plc.get_plc_data('DW100#21'))
    ## worker tick test
    while 1:
        m.worker_tick()



