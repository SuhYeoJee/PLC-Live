from PyQt5.QtWidgets import QApplication, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget
from PyQt5.QtGui import QColor

class AlarmTable(QWidget):
    def __init__(self):
        super().__init__()

        self.ALARM_TABLE = QTableWidget(self)
        self.ALARM_TABLE.setColumnCount(1)  # 열 수 설정
        self.ALARM_TABLE.setHorizontalHeaderLabels(["Alarm Status"])  # 헤더 설정

        layout = QVBoxLayout()
        layout.addWidget(self.ALARM_TABLE)
        self.setLayout(layout)

    def add_row(self, val):
        row_position = self.ALARM_TABLE.rowCount()
        self.ALARM_TABLE.insertRow(row_position)

        # 새 행에 아이템 추가
        item = QTableWidgetItem("Alarm ON" if val else "Alarm OFF")
        self.ALARM_TABLE.setItem(row_position, 0, item)

        # 배경 색상 설정
        if val:
            self.ALARM_TABLE.item(row_position, 0).setBackground(QColor(0, 255, 0))  # 초록색
        else:
            self.ALARM_TABLE.item(row_position, 0).setBackground(QColor(255, 0, 0))  # 빨간색

if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)

    window = AlarmTable()
    window.add_row(True)   # 초록색 행 추가
    window.add_row(False)  # 빨간색 행 추가
    window.resize(300, 200)
    window.show()

    sys.exit(app.exec_())
