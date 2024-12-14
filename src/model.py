if __debug__:
    import sys
    sys.path.append(r"X:\Github\PLC-Live")
# -------------------------------------------------------------------------------------------
from src.LS_PLC import LS_plc
from src.module.plcl_utils import get_now_str,get_sort_vals_by_key
from src.state import view_wait, start_wait, exit_wait
# --------------------------
PLC_IP = '192.168.0.50'
# ===========================================================================================
class Model():
    '''
    worker_tick: plc 데이터 읽기, is_next 조건 확인 : 주기적으로 실행
    '''
    def __init__(self):
        self.plc = LS_plc(PLC_IP)
        self._init_state()
        self._init_model_data()

    def _init_model_data(self)->None:
        self.graph_value = None
        self.graph_points = []
        self.alarms = {k:'off' for k in self.state.addrs["PLC_ADDR"]["ALARM"].keys()}

    def _init_state(self)->None:
        self.s_w = start_wait()
        self.e_w = exit_wait()
        self.v_w = view_wait()
        self.s_w.next_state = self.e_w
        self.e_w.next_state = self.s_w
        # --------------------------
        self.state = self.s_w # 초기상태 

    # [PLC] -------------------------------------------------------------------------------------------
    def _get_update_data(self)->dict:
        '''plc 주소에서 값 읽어 반환 {라벨:값}'''
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
    def _change_mode(self,state=None)->None:
        self.state.before_change_mode()
        if state:
            self.state = state
        else:
            self.state = self.state.next_state
        self.state.after_change_mode(get_table_data_once=self.get_table_data_once)

    def get_table_data_once(self):
        '''
        exit_wait state로 전환될 때 한 번만 실행
        table 정보를 엑셀에 저장. - 해당 정보는 갱신되지 않음
        
        '''
        read_target = self.state.addrs['TABLE_DATA']

        table_datas = {}
        for table_name,table_info in read_target.items():
            if table_name == 'PROGRAM_TABLE':
                new_datas = self.plc.read(table = table_info['table'])
                self.state.session.data["PROGRAM_TABLE"] = [{label: new_datas[base] for label, addr in  table_info['addrs'].items() if (base := addr.split('#')[0]) in new_datas}]
            else:
                new_datas = self.plc.read(table = table_info['table'])
                table_datas[table_name] = {label: new_datas[base] for label, addr in  table_info['addrs'].items() if (base := addr.split('#')[0]) in new_datas}
        else:
            self.state.session.data["PROGRAM_VIEW_TABLE"] = get_sort_vals_by_key(table_datas)
            

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

            self.state.after_worker_tick(update_data=update_data,alarm_data=alarm_data,is_graph_update=is_graph_update)

            return [update_data,alarm_data,is_graph_update]
        except Exception as e:
            print(e)
            print('model.worker_tick error')
            return [{},{},False]

    def _update_alarm(self,update_data:dict)->dict:
        '''알람 변동시 정보 반환 {arr_label:['on',timestr]}'''
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
        '''알람 상태 (on/off) 반환'''
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
        '''그래프 갱신 여부 반환'''
        if 'AUTOMATIC_ACTUAL_WORKCOUNT' not in update_data.keys():
            return False
        # 그래프 갱신 판단
        graph_value = update_data['AUTOMATIC_ACTUAL_WORKCOUNT']
        if graph_value != self.graph_value:
            self.graph_value = graph_value
            self.graph_points.append(float(update_data['AUTOMATIC_SEGSIZE_1']))
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



