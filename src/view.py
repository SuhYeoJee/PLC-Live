if __debug__:
    import sys
    sys.path.append(r"X:\Github\PLC-Live")
# -------------------------------------------------------------------------------------------
from src.module.pyqt_imports import *
from src.module.plcl_utils import get_now_str
import pyqtgraph as pg
import json
# ===========================================================================================

class View(QMainWindow, uic.loadUiType("./ui/mainwindow.ui")[0]) :
    def __init__(self) :
        super().__init__()
        self.setupUi(self)
        self.create_menu()
        self.PROGRAM_TABLE.setHorizontalHeaderLabels(["STEP\nDIMENSION","CHARGE\nDIMENSION","FWD\nTIME","SELECT\nCAR","OSC\nCOUNT","BWD\nTIME","PRESS\nPOSITION","FINAL\nPRESSURE","SELECT\nDIA"])
        self.addrs = self.get_addrs()
        self.setWindowTitle("PressMonitor")

        self.PROGRAM_LIST_TABLE.setColumnWidth(0, 50)
        self.PROGRAM_LIST_TABLE.setColumnWidth(2, 50)
        self.ALARM_TABLE.setColumnWidth(0, 100)

        self.graph_widget = pg.PlotWidget()
        self.graph_widget.setBackground('w')
        QVBoxLayout(self.graph_frame).addWidget(self.graph_widget)

    def get_addrs(self):
        '''
        json.PLC_ADDR 항목 자동으로 읽어옴
        DATASET 이름을 시트명으로, 주소명을 열제목으로 사용
        '''
        with open("./src/spec/PLC_ADDR.json", 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data["PLC_ADDR"]

    # -------------------------------------------------------------------------------------------

    def update_graph(self,graph_points):
        self.graph_width = 7

        idx = len(graph_points)-1
        self.horizontalSlider.setMinimum(0)
        self.horizontalSlider.setMaximum(idx)
        self.horizontalSlider.setValue(idx)

        self.graph_widget.plot(graph_points, pen=pg.mkPen('g', width=self.graph_width))

        try:
            self.graph_widget.removeItem(self.vertical_line)
        except: ...
        self.vertical_line = pg.InfiniteLine(pos=self.horizontalSlider.value(), angle=90, pen=pg.mkPen('r', width=2))
        self.graph_widget.addItem(self.vertical_line)
        self.horizontalSlider.valueChanged.connect(self.update_vertical_line)

    def update_vertical_line(self, value):
        '''
        슬라이더 이동시 동작
        - 세로선 갱신
        - 그래프 위치 갱신
        + set_text 갱신(view에서)
        '''
        self.vertical_line.setPos(value)
        self.graph_widget.setXRange(value - self.graph_width/2, value + self.graph_width/2)
        # 여기 VALUE값을 IDX로해서 테이블 갱신필.
        # self.c.set_load_data(value)

    # [TABLE 표시 규칙] -------------------------------------------------------------------------------------------
    def set_text_PROGRAM_TABLE(self, key, val)->None:
        '''
        PROGRAM_TABLE 표시 규칙
        '''
        i = int(''.join(filter(str.isdigit, key)))-1
        for j,item in enumerate(["STEPDIMENSION","CHARGEDIMENSION","FWDTIME","SELECTCAR","OSCCOUNT","BWDTIME","PRESSPOSITION","FINALPRESSURE","SELECTDIA"]):
            if not (item in key): continue
            self.PROGRAM_TABLE.setItem(i, j, QTableWidgetItem(val))
    # --------------------------
    def set_text_PROGRAM_LIST_TABLE(self, key, val)->None:
        '''
        PROGRAM_LIST_TABL 표시 규칙
        '''        
        i = int(''.join(filter(str.isdigit, key)))-1
        j = (i//10)*2+1
        i = i%10
        self.PROGRAM_LIST_TABLE.setItem(i, j, QTableWidgetItem(val))

        for j,item in enumerate(["STEPDIMENSION","CHARGEDIMENSION","FWDTIME","SELECTCAR","OSCCOUNT","BWDTIME","PRESSPOSITION","FINALPRESSURE","SELECTDIA"]):
            if not (item in key): continue
            self.PROGRAM_LIST_TABLE.setItem(i, j, QTableWidgetItem(val))
    # --------------------------
    def set_text_PROGRAM_VIEW_TABLE(self, key, val)->None:
        '''
        PROGRAM_VIEW_TABLE 표시 규칙
        '''
        i = int(''.join(filter(str.isdigit, key)))-1
        for j,item in enumerate(["STEPDIMENSION","CHARGEDIMENSION","FWDTIME","SELECTCAR","OSCCOUNT","BWDTIME","PRESSPOSITION","FINALPRESSURE","SELECTDIA"]):
            if not (item in key): continue
            self.PROGRAM_VIEW_TABLE.setItem(i, j, QTableWidgetItem(val))

    def set_text_ALARM_TABLE(self,key,val):
        if val == '1':
            now_time = get_now_str("%H:%M:%S")

            row_position = self.ALARM_TABLE.rowCount()
            self.ALARM_TABLE.insertRow(row_position)

            for col, value in enumerate([now_time,key]):
                self.ALARM_TABLE.setItem(row_position, col, QTableWidgetItem(str(value)))

    def set_alarm(self,alarm_data:dict)->None:
        for k,v in alarm_data.items():
            if 'ALARM' in k:
                self.set_text_ALARM_TABLE(k,v)

    def clear_alarm_table(self):
        row_count = self.ALARM_TABLE.rowCount()
        
        for row in range(row_count - 1, 0, -1):
            self.ALARM_TABLE.removeRow(row)
    # -------------------------------------------------------------------------------------------

    def set_text(self,update_data:dict)->None:
        for k,v in update_data.items():
            if 'PROGRAM_TABLE' in k: # 테이블에 값 표시
                self.set_text_PROGRAM_TABLE(k,v)
            elif 'PROGRAM_LIST_TABLE' in k:
                self.set_text_PROGRAM_LIST_TABLE(k,v)
            elif 'PROGRAM_VIEW_TABLE' in k:
                self.set_text_PROGRAM_VIEW_TABLE(k,v)
            else: # line edit에 값 표시
                try:
                    lineedit = self.findChild(QLineEdit, k, Qt.FindChildrenRecursively)
                    if lineedit:
                        lineedit.setText(str(v))
                    else: #해당 line edit 없음
                        # print(k)
                        ...
                except AttributeError as e:
                    ...
                    #print_error_box(e,k,v)

    def clear_text(self,update_data:dict=None)->None:
        if not update_data:
            update_data = {addr_name:addr_val for v in self.addrs.values() for addr_name, addr_val in v.items()}

        for k,v in update_data.items():
            if 'PROGRAM_TABLE' in k: # 테이블에 값 표시
                self.set_text_PROGRAM_TABLE(k,"")
            elif 'PROGRAM_LIST_TABLE' in k:
                self.set_text_PROGRAM_LIST_TABLE(k,"")
            elif 'PROGRAM_VIEW_TABLE' in k:
                self.set_text_PROGRAM_VIEW_TABLE(k,"")
            elif 'ALARM' in k:
                self.clear_alarm_table()
            else: # line edit에 값 표시
                try:
                    lineedit = self.findChild(QLineEdit, k, Qt.FindChildrenRecursively)
                    if lineedit:
                        lineedit.setText(str(""))
                    else: #해당 line edit 없음
                        print(k)
                except AttributeError as e:
                    ...
                    #print_error_box(e,k,v)

    # [menu] ===========================================================================================
    def create_menu(self):
        menubar = self.menuBar()
        # -------------------------------------------------------------------------------------------
        self.load_action = QAction('Load', self)
        self.close_action = QAction('Close', self)
        self.capture_action = QAction('Capture', self)
        self.print_action = QAction('Print', self)
        # --------------------------
        file_menu = menubar.addMenu('File')
        file_menu.addAction(self.load_action)
        file_menu.addAction(self.capture_action)
        file_menu.addAction(self.print_action)
        file_menu.addAction(self.close_action)
        # -------------------------------------------------------------------------------------------
        self.connect_action = QAction('Connect', self)
        self.disconnect_action = QAction('Disconnect', self)
        # --------------------------
        connection_menu = menubar.addMenu('Connection')
        connection_menu.addAction(self.connect_action)
        connection_menu.addAction(self.disconnect_action)

    def open_file_dialog(self)->str:
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File", "./result", "Excel Files (*.xlsx)", options=options)
        if file_path:
            self.file_path = file_path
        else:
            self.file_path = ''
        return self.file_path
    
    def show_alert(self, message):#plc에서 호출
        # 알림창 생성
        alert = QMessageBox(self)
        alert.setWindowTitle("PLC 연결")
        alert.setText(message)
        alert.setIcon(QMessageBox.Information)  # 알림창 아이콘 설정
        alert.setStandardButtons(QMessageBox.Ok)  # 확인 버튼 설정
        alert.exec_()  # 알림창 실행

    def change_window(self,title): #model에서 호출
        self.setWindowTitle(f"PressMonitor: {title}")
        
# ===========================================================================================
if __name__ == "__main__":
    app = QApplication([])
    window = View()
    window.show()
    app.exec_()

