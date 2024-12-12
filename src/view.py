if __debug__:
    import sys
    sys.path.append(r"X:\Github\PLC-Live")
# -------------------------------------------------------------------------------------------
from src.module.pyqt_imports import *
import pyqtgraph as pg
# ===========================================================================================

class View(QMainWindow, uic.loadUiType("./ui/mainwindow.ui")[0]) :
    def __init__(self) :
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("PressMonitor")
        self.init_menu()
        self.init_table()
        self.init_graph()
        # self.addrs = self.get_addrs()
    # --------------------------
    def init_menu(self):
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

    def init_table(self):
        self.PROGRAM_TABLE.horizontalHeader().setVisible(True)
        self.PROGRAM_VIEW_TABLE.horizontalHeader().setVisible(True)
        self.PROGRAM_TABLE.verticalHeader().setVisible(True)
        self.PROGRAM_VIEW_TABLE.verticalHeader().setVisible(True)
        self.PROGRAM_TABLE.setHorizontalHeaderLabels(["STEP\nDIMENSION","CHARGE\nDIMENSION","FWD\nTIME","SELECT\nCAR","OSC\nCOUNT","BWD\nTIME","PRESS\nPOSITION","FINAL\nPRESSURE","SELECT\nDIA"])
        self.PROGRAM_VIEW_TABLE.setHorizontalHeaderLabels(["STEP\nDIMENSION","CHARGE\nDIMENSION","FWD\nTIME","SELECT\nCAR","OSC\nCOUNT","BWD\nTIME","PRESS\nPOSITION","FINAL\nPRESSURE","SELECT\nDIA"])
        self.ALARM_TABLE.setHorizontalHeaderLabels(["TIME","ALARM","STATE"])
        self.PROGRAM_LIST_TABLE.setColumnWidth(0, 50)
        self.PROGRAM_LIST_TABLE.setColumnWidth(2, 50)
        self.ALARM_TABLE.setColumnWidth(0, 200)
    
    def init_graph(self):
        self.graph_width = 4
        self.graph_widget = pg.PlotWidget()
        self.graph_widget.setBackground('w')
        self.horizontal_val = 0
        self.set_graph_y()
        QVBoxLayout(self.graph_frame).addWidget(self.graph_widget)
        self.vertical_line = pg.InfiniteLine(pos=0, angle=90, pen=pg.mkPen('r', width=2))


    # [TABLE 라벨 매핑] ===========================================================================================
    def _set_text_PROGRAM_TABLE(self, key, val)->None:
        i = int(''.join(filter(str.isdigit, key)))-1
        for j,item in enumerate(["STEPDIMENSION","CHARGEDIMENSION","FWDTIME","SELECTCAR","OSCCOUNT","BWDTIME","PRESSPOSITION","FINALPRESSURE","SELECTDIA"]):
            if not (item in key): continue
            self.PROGRAM_TABLE.setItem(i, j, QTableWidgetItem(val))
    # --------------------------
    def _set_text_PROGRAM_LIST_TABLE(self, key, val)->None:
        idx = int(''.join(filter(str.isdigit, key)))-1
        j = (idx//10)*2+1
        i = idx%10
        self.PROGRAM_LIST_TABLE.setItem(i, j, QTableWidgetItem(val))
    
    def _set_num_PROGRAM_LIST_TABLE(self)->None:
        for idx in range(20):
            self.PROGRAM_LIST_TABLE.setItem(idx%10, (idx//10)*2, QTableWidgetItem(str(idx+1)))
        
    # --------------------------
    def _set_text_PROGRAM_VIEW_TABLE(self, key, val)->None:
        i = int(''.join(filter(str.isdigit, key)))-1
        for j,item in enumerate(["STEPDIMENSION","CHARGEDIMENSION","FWDTIME","SELECTCAR","OSCCOUNT","BWDTIME","PRESSPOSITION","FINALPRESSURE","SELECTDIA"]):
            if not (item in key): continue
            self.PROGRAM_VIEW_TABLE.setItem(i, j, QTableWidgetItem(val))
    # --------------------------
    def _set_text_ALARM_TABLE(self,key,val)->None:
        '''
        key = 'ALARM_EMERGENCY_STOP'
        val = ['on', '2024-10-20 15:44:13']
        '''
        state, timestr = val
        row_position = self.ALARM_TABLE.rowCount()
        self.ALARM_TABLE.insertRow(row_position)

        color = QColor(255, 0, 0) if state == 'on' else QColor(200, 200, 200) if state == 'off' else None
        for col, item in enumerate([QTableWidgetItem(timestr),QTableWidgetItem(key)]):
            self.ALARM_TABLE.setItem(row_position, col, item)
            if color:
                item.setBackground(color)

    # [view update] ===========================================================================================
    def set_text(self,update_data:dict)->None:
        self._set_num_PROGRAM_LIST_TABLE()
        for k,v in update_data.items():
            if (type(v) == type('')) and ('#'in v) and ('%' in v) :continue
            if 'PROGRAM_TABLE' in k: # 테이블에 값 표시
                self._set_text_PROGRAM_TABLE(k,v)
            elif 'PROGRAM_LIST_TABLE' in k:
                self._set_text_PROGRAM_LIST_TABLE(k,v)
            elif 'PROGRAM_VIEW_TABLE' in k:
                self._set_text_PROGRAM_VIEW_TABLE(k,v)
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
        QApplication.processEvents()
    # --------------------------
    def _clear_table(self,table)->None:
        for row in range(table.rowCount()):
            for col in range(table.columnCount()):
                table.setItem(row, col, QTableWidgetItem(''))
    # --------------------------
    def _clear_graph(self)->None:
        self.graph_widget.clear()
        self.set_graph_y()

    # --------------------------
    def clear_window(self)->None:
        self._clear_table(self.PROGRAM_TABLE)
        self._clear_table(self.PROGRAM_LIST_TABLE)
        self._clear_table(self.PROGRAM_VIEW_TABLE)
        self._clear_table(self.ALARM_TABLE)
        self._clear_graph()
        for line_edit in self.findChildren(QLineEdit):
            line_edit.clear()
    # --------------------------
    def set_alarm(self,alarm_datas:dict)->None:
        for alarm_name,alarm_data in alarm_datas.items():
            self._set_text_ALARM_TABLE(alarm_name,alarm_data)     
    # --------------------------

    def set_graph_y(self,y:float=0.0):
        self.horizontal_val = y
        self.graph_widget.setYRange(float(self.horizontal_val)-0.2,float(self.horizontal_val)+0.2)
        self.horizontal_line = pg.InfiniteLine(pos=self.horizontal_val, angle=0, pen=pg.mkPen('k', width=2))
        self.graph_widget.addItem(self.horizontal_line)


    def update_graph(self,graph_points:list):
        '''
        리스트 값을 그래프에 표기
        슬라이더 세팅
        '''
        idx = len(graph_points)-1
        self.horizontalSlider.setMinimum(0)
        self.horizontalSlider.setMaximum(idx)
        self.horizontalSlider.setValue(idx)

        self.graph_widget.plot(graph_points, pen=pg.mkPen('g', width=self.graph_width))
        try: #기존 세로선 삭제
            self.graph_widget.removeItem(self.vertical_line)
        except: ...
        self.vertical_line = pg.InfiniteLine(pos=self.horizontalSlider.value(), angle=90, pen=pg.mkPen('r', width=2))
        self.graph_widget.addItem(self.vertical_line)

    # [external call] ===========================================================================================
    def open_file_dialog(self)->str:
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File", "./result", "Excel Files (*.xlsx)", options=options)
        if file_path:
            self.file_path = file_path
        else:
            self.file_path = ''
        return self.file_path
    # --------------------------
    def show_alert(self, message):
        # 알림창 생성
        alert = QMessageBox(self)
        alert.setWindowTitle("PLC 연결")
        alert.setText(message)
        alert.setIcon(QMessageBox.Information)  # 알림창 아이콘 설정
        alert.setStandardButtons(QMessageBox.Ok)  # 확인 버튼 설정
        alert.exec_()  # 알림창 실행
    # --------------------------
    def change_window_title(self,title): 
        self.setWindowTitle(f"PressMonitor: {title}")

# ===========================================================================================


# ===========================================================================================
if __name__ == "__main__":
    app = QApplication([])
    v = View()
    v.show()
    app.exec_()

