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
                tick_data = self.model.worker_tick()
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

        # [action mapping] --------------------------
        self.view.capture_action.triggered.connect(self.capture_data)
        self.view.print_action.triggered.connect(self.print_data)
        self.view.load_action.triggered.connect(self.load_data)
        self.view.close_action.triggered.connect(self.close_data)
        self.view.connect_action.triggered.connect(self.connect_plc)
        self.view.disconnect_action.triggered.connect(self.disconnect_plc)
    # -------------------------------------------------------------------------------------------

    # --------------------------
    def start_monitoring(self)->None:
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
        self.model.c_w.use_tick=True
        self.model.state = self.model.c_w
        self.start_monitoring()

    def disconnect_plc(self):
        self.model.c_w.use_tick=False
        self.model.state.before_change_mode()
        self.model.state = self.model.c_w
        print(f'_change_mode:{type(self.model.state).__name__}')
        self.exit_monitoring()

    def load_data(self): #엑셀 파일열기
        self.model.c_w.use_tick=False
        file_name = self.view.open_file_dialog()
        self.model.v_w = view_wait(file_name)
        self.model.state = self.model.v_w
        self.set_load_data(-1)

    # idx값으로 테이블 세팅하기
    # 이거를.. 뷰에서 역호출 하면 안되지 않나
    def set_load_data(self,idx): #엑셀에서 값세팅: view에서 호출
        for key, val in self.model.v_w.session.data.items():
            target = val[idx] # 마지막값 -> 이거 인덱스 값으로 전환
            self.view.set_text(target)

    def close_data(self):
        self.view.clear_window()
        self.model.state = self.model.c_w

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


