if __debug__:
    import sys
    sys.path.append(r"X:\Github\PLC-Live")
# -------------------------------------------------------------------------------------------
from src.module.pyqt_imports import *
from src.module.plcl_utils import get_now_str, is_float_str
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
                # import pprint
                # pprint.pprint(tick_data)
                # print('########################################')
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
            self.model.graph_points = []
            self.worker = Worker(self.model,self.worker_time)
            self.worker.data_generated.connect(self._update_view)  
            self.worker.start()
    # --------------------------
    def _update_view(self,tick_data):
        update_data,alarm_data,is_graph_update = tick_data
        self.view.set_text(update_data)


        is_next = self.model.state._is_next(update_data[self.model.state.key]) # 읽은 항목에서 state체크
        if is_next: # state 넘어가기
            self.change_mode()

        if is_graph_update:
            print(self.model.graph_points)
            if is_float_str(update_data['AUTOMATIC_SET_PRESSINGSIZE']):
                self.view.set_graph_y(update_data['AUTOMATIC_SET_PRESSINGSIZE'])
            self.view.update_graph(self.model.graph_points)

        if alarm_data:
            print(alarm_data)
            self.view.set_alarm(alarm_data)
    # --------------------------
    def exit_monitoring(self)->None:
        self.model.graph_points = []
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

    def _init_alarm_from_session_data(self):
        try:
            alarm_datas = self.model.state.session.data['_alarm']
            self.view.set_alarm(alarm_datas)
        except KeyError:
            ...

    def _init_graph_from_session_data(self):
        # set horiz_line
        graph_y = [x['AUTOMATIC_SET_PRESSINGSIZE'] for x in self.model.state.session.data['AUTOMATIC'] if is_float_str(x['AUTOMATIC_SET_PRESSINGSIZE'])]
        [self.view.set_graph_y(y) for y in graph_y if is_float_str(y)]
        
        # set graph
        graph_points = [float(x['AUTOMATIC_SEGSIZE_1']) for x in self.model.state.session.data['_graph'] if is_float_str (x['AUTOMATIC_SEGSIZE_1'])]
        self.view.update_graph(graph_points)

    def load_data(self): #엑셀 파일열기
        file_name = self.view.open_file_dialog()
        self.change_mode(view_wait(file_name))
        self._init_alarm_from_session_data()
        self._init_graph_from_session_data()
        self.slider_update(0)

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

        self.model._change_mode(state)
        self.model._init_model_data()

        if state == self.model.s_w: #클리어 안함
            ...
        elif clear:
            self.view.clear_window() # 확인 후 클리어

        try:
            title_str =f'{str(type(self.model.state).__name__)} - {str(self.model.state.session.file_name)}'
        except:
            title_str =f'{str(type(self.model.state).__name__)}'
        self.view.change_window_title(title_str)
        print(f'_change_mode:{type(self.model.state).__name__}')



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


