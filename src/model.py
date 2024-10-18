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
        self.alarms = {} # {label:'on', label:'off'}
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
        self.state = self.s_w # debug

    # [PLC] -------------------------------------------------------------------------------------------
    def _get_update_data(self)->dict:
        new_datas,result = {}, {}
        table_data = {
            # 'PROGRAM':{"start_addr" : "%DW2100","size" : 384}, # DW2100 ~ DW2109 ~ DW2330 ~ DW2339
            'PROGRAM':{"%DW2100" : 10,"%DW2110" : 10, }, # DW2100 ~ DW2109 ~ DW2330 ~ DW2339
            'PROGRAM_LIST':["%DW8090#10S00","%DW8360#10S00",],
            'PROGRAM_VIEW':{"%DW5100" : 10}, # DW5100 ~ DW5109 ~ DW5330 ~ DW5339
        
        }

        for k,v in self.state.dataset.items():
            if 'PROGRAM' in k: # table
                if isinstance(table_data[k], list):
                    new_datas.update(self.plc.read(single=table_data[k]))
                else:
                    addrs = [addr for label, addr in v.items() if 'TABLE' in label]
                    for start_addr,read_size in table_data[k].items():
                        new_datas.update(self.plc.read(table={"addrs":addrs,"start_addr":start_addr,"size":read_size}))
            addrs = [addr for label,addr in v.items() if 'TABLE' not in label]
            new_datas.update(self.plc.read(single=addrs))
            result.update({label: new_datas[base] for label, addr in v.items() if (base := addr.split('#')[0]) in new_datas})
            print(result)
        return result

    def _change_mode(self)->None:
        print(f'_change_mode:{type(self.state).__name__}')
        self.state.before_change_mode()
        self.state = self.state.next_state
        self.state.after_change_mode()

    def worker_tick(self)->dict:
        '''
        1. PLC 데이터 갱신
        2. state 전환
        '''
        self.state.before_worker_tick()

        update_data = self._get_update_data() # plc 데이터 읽기
        alarm_data = self._update_alarm(update_data)
        is_graph_update = self._update_graph(update_data)

        is_next = self.state._is_next(update_data[self.state.key]) # 읽은 항목에서 state체크
        if is_next: # state 넘어가기
            self._change_mode()
        self.state.after_worker_tick(update_data=update_data)

        from pprint import pprint
        pprint(update_data)
        pprint(alarm_data)
        pprint(is_graph_update)


        return update_data,alarm_data,is_graph_update

    def _update_alarm(self,update_data:dict)->dict:
        result = {}
        if 'alarm' not in update_data.keys():
            return result
        
        # 알람 on off 판단 (함수 분리 필)
        alarms = {}
        for label,plc_addr in self.state.addrs['alarm'].items():
            addr, _, option = plc_addr.partition('#')
            value = update_data['alarm'][label]
            if option[2] == "a":
                alarms[label] = 'on' if value == 1 else 'off'
            elif option[2] == "A":
                alarms[label] = 'off' if value == 1 else 'on'
        
        # 기존 상태와 비교
        for label,value in alarms.items():
            try:
                if value != self.alarms[label]:
                    result[label] = [value,get_now_str()]
            except IndexError:
                result[label] = [value,get_now_str()]
        else:
            self.alarms = alarms

        return result #{arr_label:['on',timestr]}

    def _update_graph(self,update_data)->bool:
        if 'AUTOMATIC' not in update_data.keys():
            return False
        
        # 그래프 갱신 판단
        graph_value = self.state.addrs['AUTOMATIC']['graph_addr']
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
    # for i in range(100):
    #     print(m.worker_tick())

    while 1:
        m.worker_tick()