
from typing import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import Qt

# 分别表示上下左右
ActionsDict = {
    0 : [[-1, 0], '👆'],
    1 : [[1, 0], '👇'],
    2 : [[0, -1], '👈'],
    3 : [[0, 1], '👉']
}
# 每秒自动走几格
CellSpeed = 3

class Walker(QObject):
    sendMsg = pyqtSignal(str)
    stepSignal = pyqtSignal()
    toleUseSignal = pyqtSignal()
    canPressedAutoMoveBtn = pyqtSignal(bool)  # 在自动行走没结束前，禁用两个策略按钮
    stillMovable = pyqtSignal(int)

    def __init__(self, x : int, y : int, tolerance : int):
        # self.stepLimited = stepLimited  这个可以用来拓展，我是这么想的：比如让移动有次数限制
        super().__init__()
        self.x = x
        self.y = y
        self.tolerance = tolerance
        self.tolerance_backup = tolerance
        self.autoTimer = QTimer()
        self.stillMovable.connect(self.stopTimerToReocordById)

    def reset(self, x: int, y: int, tolerance: int):
        self.x, self.y = x, y
        self.tolerance = tolerance
        self.tolerance_backup = tolerance

    # 检测是否会被惩罚
    @staticmethod
    def _judge_penalty(grids: list[list[int]], x : int, y : int) -> bool: return grids[x][y] == 2

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

    def move(
            self,
            dx : int,
            dy : int,
            row : int,
            column : int,
            grids : List[List[int]],
            where : str,
            updateLoc : Callable
    ) -> None:
        new_x = self.x + dx
        new_y = self.y + dy
        self.stepSignal.emit()
        self.canPressedAutoMoveBtn.emit(False)
        # 边界检查
        if 0 <= new_x < row and 0 <= new_y < column:
            if self._judge_not_forbidden_area(grids, new_x, new_y):
                self.x = new_x
                self.y = new_y
                updateLoc()
                self.sendMsg.emit(f'成功往 [{where}] 走了一步')
                if self._judge_penalty(grids, new_x, new_y):
                    self.tolerance -= 1
                    self.sendMsg.emit('被惩罚一次！')
                    self.toleUseSignal.emit()
                if not self._judge_acceptable_punishment():
                    self.stillMovable.emit(0)
                if self._judge_is_end(grids, new_x, new_y):
                    self.stillMovable.emit(1)
        else:
            self.sendMsg.emit('已到达边界！')

    # 根据行为序列自动行走
    def autoMove(self, actions: Iterator[int], row: int, column: int, grids: List[List[int]], updateLoc: Callable) -> None:
        self.autoTimer.start(1000 // CellSpeed)
        self.autoTimer.timeout.connect(lambda: self.__set_step_visible(actions, row, column, grids, updateLoc))

    # 让每一步都清晰可见
    def __set_step_visible(self, actions : Iterator, row: int, column: int, grids: List[List[int]], updateLoc: Callable) -> None:
        try:
            deltas, where = ActionsDict[next(actions)]
            self.move(deltas[0], deltas[1], row, column, grids, where, updateLoc)
        except StopIteration:
            self.stillMovable.emit(2)

    # 对各种结束方式的记录以及让计时器结束，从头调用策略
    def stopTimerToReocordById(self, getId : int) -> None:
        self.autoTimer.stop()
        self.canPressedAutoMoveBtn.emit(True)  # 恢复按钮
        # 根据 id记录策略执行情况
        if getId == 0:
            self.sendMsg.emit("因无法再惩罚而结束！")
        elif getId == 1:
            self.sendMsg.emit("因成功到达终点而结束！")
        elif getId == 2:
            self.sendMsg.emit('计时器已执行完全部动作！')

    # 强化学习接口，用于训练walker行走，还在开发中
    def policy(self): ...
