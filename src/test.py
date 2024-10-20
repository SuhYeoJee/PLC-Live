import sys
import time
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import QThread, pyqtSignal

# 모델 클래스
class HardwareModel:
    def __init__(self):
        self.state = True  # 모델의 상태 초기값

    def communicate_with_hardware(self):
        print("Communicating with hardware...")
        time.sleep(10)  # 10초 대기, 하드웨어와의 통신 시뮬레이션
        print("Communication complete.")

# 워커 클래스
class CommunicationWorker(QThread):
    finished = pyqtSignal()  # 통신 완료 신호

    def __init__(self, model):
        super().__init__()
        self.model = model
        self.running = True

    def run(self):
        while self.running:
            if self.model.state:  # 모델의 상태가 True인 경우
                self.handle_true_state()  # 상태가 True일 때의 처리
            else:
                self.handle_false_state()  # 상태가 False일 때의 처리
            self.msleep(5000)  # 5초 대기

    def handle_true_state(self):
        self.model.communicate_with_hardware()  # 모델의 통신 메서드 호출
        self.finished.emit()  # 통신 완료 신호 전송

    def handle_false_state(self):
        print("model state: False")  # 상태가 False일 경우 출력

    def stop(self):
        self.running = False

# 뷰 클래스
class HardwareView(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        self.layout = QVBoxLayout()

        self.label = QLabel('Waiting for communication...', self)
        self.layout.addWidget(self.label)

        self.start_button = QPushButton('Start Communication', self)
        self.layout.addWidget(self.start_button)

        self.stop_button = QPushButton('Stop Communication', self)
        self.layout.addWidget(self.stop_button)

        self.setLayout(self.layout)
        self.setWindowTitle('Hardware Communication')

# 컨트롤러 클래스
class HardwareController:
    def __init__(self, view, model):
        self.view = view
        self.model = model
        self.worker = None  # 워커 초기화

        # 버튼 클릭 시 통신 시작
        self.view.start_button.clicked.connect(self.start_communication)
        self.view.stop_button.clicked.connect(self.stop_communication)

    def start_communication(self):
        if self.worker is None or not self.worker.isRunning():
            self.view.label.setText('Starting communication...')
            self.worker = CommunicationWorker(self.model)  # 새로운 워커 인스턴스 생성
            self.worker.finished.connect(self.update_view)  # 신호 연결
            self.worker.start()  # 워커 스레드 시작

    def stop_communication(self):
        self.view.label.setText('Stopping communication...')
        if self.worker is not None:
            self.worker.stop()  # 워커 중지

    def update_view(self):
        self.view.label.setText('Communication completed.')

if __name__ == "__main__":
    app = QApplication(sys.argv)

    model = HardwareModel()
    view = HardwareView()
    controller = HardwareController(view, model)

    view.show()
    sys.exit(app.exec_())
