if __debug__:
    import sys
    sys.path.append(r"X:\Github\PLC-Live")
# -------------------------------------------------------------------------------------------
from src.module.pyqt_imports import *
from src.module.plcl_utils import get_now_str
from src.model import Model
from src.view import View    
from src.module.pyqt_imports import *
from src.state import view_wait
# --------------------------
import subprocess
from os import makedirs
import ast
# ===========================================================================================
class Worker(QThread):
    data_generated = pyqtSignal(list)

    def __init__(self,model,time:int=5000):
        super().__init__()
        self.model = model
        self.time = time
        self.running = True

    def run(self):
        while self.running:
            if self.model.state.use_tick: #틱갱신
                print('#################tick###################')
                tick_data = self.model.worker_tick() # update_data,alarm_data,is_graph_update
                import pprint
                pprint.pprint(tick_data)
                print('########################################')
                self.data_generated.emit(tick_data)
            self.msleep(self.time)

    def stop(self):
        self.running = False

# ===========================================================================================
class Controller:
    def __init__(self,model,view):
        self.worker_time = 5000 # set worker time (1000 = 1 sec.)
        self.model = model
        self.view = view
        self.worker = None
        self.graph_points = []
        self._view_action_mapping()

    def _view_action_mapping(self):
        self.view.capture_action.triggered.connect(self.capture_data)
        self.view.print_action.triggered.connect(self.print_data)
        self.view.load_action.triggered.connect(self.load_data)
        self.view.close_action.triggered.connect(self.close_data)
        self.view.connect_action.triggered.connect(self.connect_plc)
        self.view.disconnect_action.triggered.connect(self.disconnect_plc)
        self.view.horizontalSlider.valueChanged.connect(self.slider_update)
        
    # -------------------------------------------------------------------------------------------
    def start_monitoring(self)->None:
        self.view.clear_window()
        if self.worker is None or not self.worker.isRunning():
            self.graph_points = []
            self.worker = Worker(self.model,self.worker_time)
            self.worker.data_generated.connect(self._update_view)  
            self.worker.start()
    # --------------------------
    def _update_view(self,tick_data):
        update_data,alarm_data,is_graph_update = tick_data
        self.view.set_text(update_data)

        if is_graph_update:
            self.view.set_graph_y(update_data['AUTOMATIC_SET_PRESSINGSIZE'])
            self.graph_points.append(float(update_data['AUTOMATIC_SEGSIZE_1']))
            print(self.graph_points)
            self.view.update_graph(self.graph_points)

        if alarm_data:
            print(alarm_data)
            self.view.set_alarm(alarm_data)
    # --------------------------
    def exit_monitoring(self)->None:
        self.graph_points = []
        if self.worker is not None:
            self.worker.stop()

    # [매핑함수] ===========================================================================================
    def capture_data(self):
        print('&capture_data')
        screenshot = QApplication.primaryScreen().grabWindow(self.view.winId())
        try:
            file_name = ((self.model.state.session.file_name).split('/')[-1]).split('.')[0]
        except Exception as e:
            file_name = get_now_str("%Y-%m-%d_%H-%M-%S")
        img_name = file_name + '.png'
        img_path = './capture/' + img_name
        # --------------------------
        makedirs('./capture', exist_ok=True)
        screenshot.save(img_path, 'png')
        return img_name

    def print_data(self):
        print('&print_data')
        img_name = self.capture_data()
        subprocess.run(["start", "mspaint", "/p",img_name], shell=True, cwd='./capture')

    def connect_plc(self):
        self.change_mode(self.model.s_w)
        self.start_monitoring()

    def disconnect_plc(self):
        self.exit_monitoring()
        self.change_mode(view_wait(),False)

    # def _init_graph_points_from_session_data(self,idxs):
    #     graph_idxs = [int(x['graph']) for x in idxs]
    #     graph_points = [self.model.state.session.data['graph'][x-1]['AUTOMATIC_SEGSIZE_1'] for x in graph_idxs]
    #     graph_y = [self.model.state.session.data['AUTOMATIC'][x-1]['AUTOMATIC_SET_PRESSINGSIZE'] for x in graph_idxs]
    #     [self.view.set_graph_y(y) for y in graph_y]
        
    #     return graph_points
    
    # def _view_update_data_from_session_data(self,idx:int=-1):
    #     update_data = {}
    #     for sheet,sheet_idx in self.idxs[idx].items():
    #         if sheet in ['idx','graph','ALARM']:
    #             continue
    #         update_data.update(self.model.state.session.data[sheet][sheet_idx-1])
    #     self.view.set_text(update_data)

    # def _init_idxs(self)->list:
    #     '''
    #     [{'ALARM': 1,'AUTOMATIC': 1,'SYSTEM': 1,'graph': 0,'idx': 0},
    #     {'ALARM': 3,'AUTOMATIC': 3,'SYSTEM': 3,'graph': 3,'idx': 1},]
    #     '''
    #     def to_int(idx):
    #         try:
    #             int(idx)
    #         except:
    #             return 0
    #         else:
    #             return int(idx)
    #     result = [{sheet: to_int(idx) for sheet, idx in idx_line.items()} for idx_line in self.model.state.session.data['idx'] if idx_line]
    #     return result[1:]

    # def _init_alarm_from_session_data(self):
    #     alarm_datas = self.model.state.session.data['alarm_list']
    #     for alarm_data in alarm_datas:
    #         for k,v in alarm_data.items():
    #             self.view.set_alarm({k:ast.literal_eval(v)}) 


    def load_data(self): #엑셀 파일열기
        file_name = self.view.open_file_dialog()
        self.change_mode(view_wait(file_name))

        self.idxs = self._init_idxs()
        self.graph_points = [float(x) for x in self._init_graph_points_from_session_data(self.idxs)[1:]]
        self.view.update_graph(self.graph_points)

        self.slider_update(0)
        self.slider_update(1)
        self._init_alarm_from_session_data()

    def slider_update(self, value): #슬라이더 갱신
        '''
        슬라이더 이동시 동작
        - 세로선 갱신
        - 그래프 위치 갱신
        - set_text 갱신
        '''
        if self.model.state == self.model.v_w:
            self.view.vertical_line.setPos(value)
            self.view.graph_widget.setXRange(value - self.view.graph_width/2, value + self.view.graph_width/2)
            self.view.graph_widget.setYRange(float(self.view.horizontal_val)-0.2,float(self.view.horizontal_val)+0.2)
            self._view_update_data_from_session_data(value)
            
    def change_mode(self,state=None,clear:bool=True):
        self.view.clear_window()
        self.model._change_mode(state)
        self.view.change_window_title(str(type(self.model.state).__name__))

    def close_data(self):
        self.change_mode()

# ===========================================================================================


def main():
    app = QApplication(sys.argv)
    model = Model()
    view = View()
    controller = Controller(model, view)

    view.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()


