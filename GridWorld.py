import sys
from typing import Optional, List, Callable

from PyQt5.QtGui import QKeyEvent
from PyQt5.QtCore import pyqtSignal, QObject, QSize, QRectF, Qt
from PyQt5.QtWidgets import (
    QSplitter, QWidget, QLabel, QLCDNumber, QGraphicsRectItem,
    QVBoxLayout, QHBoxLayout, QDialog, QPushButton, QMainWindow,
    QPlainTextEdit, QGraphicsScene, QApplication, QGraphicsView
)

from CellGens import generate_grid
class Walker(QObject):
    sendMsg = pyqtSignal(str)
    stepSignal = pyqtSignal()
    toleUseSignal = pyqtSignal()
    def __init__(self, x : int, y : int, tolerance : int):
        # self.stepLimited = stepLimited  这个可以用来拓展，我是这么想的：比如让移动有次数限制
        super().__init__()
        self.x = x
        self.y = y
        self.tolerance = tolerance
        self.tolerance_backup = tolerance

    def reset(self, x: int, y: int, tolerance: int):
        self.x = x
        self.y = y
        self.tolerance = tolerance
        self.tolerance_backup = tolerance

    # 检测是否会被惩罚
    def _judge_penalty(self, grids: list[list[int]], x : int, y : int) -> None:
        if grids[x][y] == 2:
            self.tolerance -= 1
            self.sendMsg.emit('被惩罚一次！')
            self.toleUseSignal.emit()

    # 检测是否不是禁行区
    def _judge_not_forbidden_area(self, grids: list[list[int]], x : int, y : int) -> bool:
        if grids[x][y] == 1:
            self.sendMsg.emit("禁止区域!")
            return False
        else:
            return True

    # 检测是否到达终点
    def _judge_is_end(self, grids: list[list[int]], x : int, y : int) -> bool:
        if grids[x][y] == 4:
            self.sendMsg.emit("suc")
            return True
        return False

    # 检测是否还能接受惩罚项
    def _judge_acceptable_punishment(self) -> bool:
        if self.tolerance < 0:
            self.sendMsg.emit("fail")
            return False
        else:
            return True


    def move(self, dx : int, dy : int, row : int, column : int, grids : List[List[int]], where : str) -> None:
        new_x = self.x + dx
        new_y = self.y + dy

        # 边界检查
        if 0 <= new_x < row and 0 <= new_y < column:
            if self._judge_not_forbidden_area(grids, new_x, new_y):
                self.x = new_x
                self.y = new_y
                self._judge_penalty(grids, new_x, new_y)
                if self._judge_acceptable_punishment() and not self._judge_is_end(grids, new_x, new_y):
                    where : str
                    self.sendMsg.emit(f'成功往 [{where}] 走了一步')
                    self.stepSignal.emit()
        else:
            self.sendMsg.emit('已到达边界！')

    # 强化学习接口，用于训练walker行走，还在开发中
    def policy(self): ...

class Scene(QGraphicsScene):
    CellColors = {
        0: Qt.white,
        1: Qt.gray,
        2: Qt.yellow,
        3: Qt.blue,
        4: Qt.black,
        5: Qt.red  # 移动单元颜色
    }

    def __init__(self, sceneSize: QSize, grids: List[List[int]], start_point: List[int], walker: Walker):
        super().__init__()
        self.sceneSize = sceneSize
        self.row = len(grids)
        self.column = len(grids[0])
        self.sceneWidth, self.sceneHeight = sceneSize.width(), sceneSize.height()
        self.cellWidth, self.cellHeight = self.sceneWidth / self.column, self.sceneHeight / self.row
        self.grids = grids
        self.start_point = start_point
        self.walker = walker
        self.walkerItem = None
        self.buildScene()
        self.update_walker_position()

    def reset(self, setNewGrids : bool = False, num_obstacles : int = 0, num_penalty : int = 0, num_endpoints : int = 0) -> None:
        # setNewGrids设置新的、同形状的二维数组
        self.walker.reset(self.start_point[0], self.start_point[1], self.walker.tolerance_backup)
        if setNewGrids:
            self.grids, self.start_point = generate_grid(self.column, self.row, num_obstacles, num_penalty, num_endpoints)
            self.walker.x = self.start_point[0]
            self.walker.y = self.start_point[1]
        self.buildScene()
        self.update_walker_position()

    def buildScene(self) -> None:
        self.clear()
        for r in range(self.row):
            for c in range(self.column):
                rect = QGraphicsRectItem(c * self.cellWidth, r * self.cellHeight, self.cellWidth, self.cellHeight)
                rect.setBrush(self.CellColors[self.grids[r][c]])
                self.addItem(rect)
        self.walkerItem = QGraphicsRectItem(QRectF(0, 0, self.cellWidth, self.cellHeight))
        self.walkerItem.setBrush(self.CellColors[5])
        self.addItem(self.walkerItem)

    def update_walker_position(self) -> None:
        self.walkerItem.setPos(self.walker.y * self.cellWidth, self.walker.x * self.cellHeight)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key_Up:
            self.walker.move(-1, 0, self.row, self.column, self.grids, '👆')
        elif event.key() == Qt.Key_Down:
            self.walker.move(1, 0, self.row, self.column, self.grids, '👇')
        elif event.key() == Qt.Key_Left:
            self.walker.move(0, -1, self.row, self.column, self.grids, '👈')
        elif event.key() == Qt.Key_Right:
            self.walker.move(0, 1, self.row, self.column, self.grids, '👉')
        self.update_walker_position()

class InfoDlg(QDialog):
    def __init__(self, reset_func : Callable, msg : str, cancel_func : Optional[Callable] = None):
        super().__init__()
        self.reset_func = reset_func
        self.cancel_func = cancel_func if cancel_func else lambda : self.close()
        self.label = QLabel(msg)
        self.btnOk = QPushButton()
        self.btnCancel = QPushButton()
        self.setUI()

    def okfunc(self):
        self.reset_func()
        self.close()

    def setUI(self) -> None:
        self.btnOk.setText('Ok')
        self.btnOk.clicked.connect(self.okfunc)
        self.btnCancel.setText('No')
        self.btnCancel.clicked.connect(self.cancel_func)
        self.setWindowFlags(Qt.FramelessWindowHint)

        hlay = QHBoxLayout()
        hlay.addWidget(self.btnOk)
        hlay.addWidget(self.btnCancel)
        vlay = QVBoxLayout()
        vlay.addWidget(self.label)
        vlay.addLayout(hlay)
        self.setLayout(vlay)
        self.setObjectName('InfoDlg')

class InfoBoard(QWidget):
    def __init__(self, tolerance : int):
        super().__init__()
        self.step = 0
        self.toleCount = 0
        self.toleLeft = tolerance
        self.stepsRecord = QLabel('已走步数')
        self.toleCountRecord = QLabel('惩罚计数')
        self.toleLeftRecord = QLabel('剩余惩罚')
        self.stepLCD = QLCDNumber()
        self.toleCountLCD = QLCDNumber()
        self.toleLeftLCD = QLCDNumber()

        self.setUI()

    def setUI(self) -> None:
        hlay1 = QHBoxLayout()
        hlay2 = QHBoxLayout()
        hlay3 = QHBoxLayout()
        vlay = QVBoxLayout()

        hlay1.addWidget(self.stepsRecord)
        hlay1.addWidget(self.stepLCD)

        hlay2.addWidget(self.toleCountRecord)
        hlay2.addWidget(self.toleCountLCD)

        hlay3.addWidget(self.toleLeftRecord)
        hlay3.addWidget(self.toleLeftLCD)
        vlay.addLayout(hlay1)
        vlay.addLayout(hlay2)
        vlay.addLayout(hlay3)
        self.setLayout(vlay)

        self.stepLCD.display(self.step)
        self.toleLeftLCD.display(self.toleLeft)
        self.toleCountLCD.display(self.toleCount)

    def step_record(self):
        self.step += 1
        self.stepLCD.display(self.step)
    def toleCount_record(self):
        self.toleCount += 1
        self.toleCountLCD.display(self.toleCount)
    def toleLeft_record(self):
        self.toleLeft -= 1
        self.toleLeftLCD.display(self.toleLeft)
    def tole_record(self):
        self.toleCount_record()
        self.toleLeft_record()

    def reset(self, tolerance: int) -> None:
        self.step = 0
        self.toleCount = 0
        self.toleLeft = tolerance
        self.stepLCD.display(0)
        self.toleLeftLCD.display(tolerance)
        self.toleCountLCD.display(0)

class AppCore(QMainWindow):

    receiveMsg = pyqtSignal()

    def __init__(
            self,
            width: int,
            height: int,
            grids: List[List[int]],
            start_point: List[int],
            tolerance: int,
            *,
            setNewGrids : bool = False,
            num_obstacles : int = 0,
            num_penalty : int = 0,
            num_endpoints : int = 0
    ):
        super().__init__()
        self.setWindowTitle('Grid Walker For RL')
        self.walker = Walker(start_point[0], start_point[1], tolerance)
        self.scene = Scene(QSize(width, height), grids, start_point, self.walker)
        self.view = QGraphicsView(self.scene)
        self.msgBox = QPlainTextEdit()
        self.infoBoard = InfoBoard(tolerance)
        self.splitter1 = QSplitter()
        self.splitter2 = QSplitter()

        self.setNewGrids = setNewGrids
        self.num_obstacles = num_obstacles
        self.num_penalty = num_penalty
        self.num_endpoints = num_endpoints
        self.setUI()

    def setUI(self):
        self.view.setObjectName('view')
        self.msgBox.setObjectName('msgBox')

        lay = QVBoxLayout()
        lay.addWidget(self.splitter1)
        self.setLayout(lay)

        self.splitter1.addWidget(self.view)
        self.splitter1.setOrientation(Qt.Horizontal)
        self.splitter1.addWidget(self.infoBoard)

        self.splitter2.addWidget(self.splitter1)
        self.splitter2.addWidget(self.msgBox)
        self.splitter2.setOrientation(Qt.Vertical)
        self.setCentralWidget(self.splitter2)

        self.msgBox.setPlaceholderText('等待运行中……')
        self.msgBox.setReadOnly(True)

        self.walker.sendMsg.connect(self.handle_msg)
        self.walker.stepSignal.connect(self.infoBoard.step_record)
        self.walker.toleUseSignal.connect(self.infoBoard.tole_record)

    def reset(self):
        self.scene.reset(self.setNewGrids, self.num_obstacles, self.num_penalty, self.num_endpoints)
        self.infoBoard.reset(self.walker.tolerance_backup)

    def handle_msg(self, msg : str):
        if msg == "suc":
            dlg = InfoDlg(self.reset, "到达终点，获胜！再来一局？")
            dlg.exec_()
            self.msgBox.clear()
            self.msgBox.setPlaceholderText('等待运行中……')
        elif msg == "fail":
            dlg = InfoDlg(self.reset, '不在规定要求内，要不重新来一局？')
            dlg.exec_()
            self.msgBox.clear()
            self.msgBox.setPlaceholderText('等待运行中……')
        else:
            self.msgBox.appendPlainText(msg)

def main(
        grids : List[List[int]],
        start_point : List[int],
        width : int = 1000,
        height : int = 800,
        tolerance : int = 20,
        *,
        setNewGrids: bool = False,
        num_obstacles: int = 0,
        num_penalty: int = 0,
        num_endpoints: int = 0
):
    app = QApplication(sys.argv)
    app.setStyleSheet(open('style.css', 'r').read())
    ui = AppCore(
        width=width,
        height=height,
        grids=grids,
        start_point=start_point,
        tolerance=tolerance,
        setNewGrids=setNewGrids,
        num_endpoints=num_endpoints,
        num_obstacles=num_obstacles,
        num_penalty=num_penalty
    )
    ui.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    Grids = generate_grid(15, 15, 40, 20, 2)
    main(Grids[0], Grids[1], setNewGrids=False, num_obstacles=40, num_penalty=20, num_endpoints=2)

