from typing import *
from abc import abstractmethod

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtCore import Qt

from MsgBox import MsgBox
from GlobalSetting import *

# 功能更新
class ResetMixin:
    @abstractmethod
    def reset(self) -> None:
        pass

# 模拟训练单元
class Walker(QObject, ResetMixin):
    msgSignal = pyqtSignal(str)  # 消息反馈器
    punishSignal = pyqtSignal()  # 惩罚反馈器
    stepSignal = pyqtSignal()  # 步行反馈器

    def __init__(self, start: List[int], tolerance : int, step : int, **kwargs):
        super().__init__(**kwargs)
        self.timer = QTimer()
        self.timer.setInterval(1000 // Speed)
        self.row, self.column = start  # 当前位置
        self.tolerance = tolerance  # 惩罚项剩余
        self.step = step  # 步数允许
        self.init_info_backup = dict(
            start=start,
            tolerance=tolerance,
            step=step
        )  # 仅备份与改变值相关的数据，不变的不用备份

    # 重置改变值
    def reset(self) -> None:
        self.tolerance = self.init_info_backup['tolerance']
        self.row, self.column = self.init_info_backup['start']
        self.step = self.init_info_backup['step']

    # 检测
    # 碰壁检测（包含禁行区域与边缘）
    @staticmethod
    def hit_the_wall(row : int, column : int) -> bool:
        return row < 0 or row >= Row or column < 0 or column >= Column or Worlds[row][column] == 2

    # 惩罚检测
    @staticmethod
    def should_punish(row : int, column : int) -> bool: return Worlds[row][column] == 1

    # 能继续惩罚
    def can_punish(self) -> bool: return self.tolerance > 0

    # 找到终点
    @staticmethod
    def reach_end(row : int, column : int) -> bool: return Worlds[row][column] == 4

    # 还有步数可走吗
    def have_step(self) -> bool:
        return self.step > 0

    # 行走，每次行走反馈一个状态码
    # 目前：0表示成功退出、1和2表示失败告终、3表示可继续行走
    def move(self, direction : str) -> Literal[0, 1, 2, 3]:
        deltas, where = MoveDirections.get(direction)
        newRow, newColumn = self.row + deltas[0], self.column + deltas[1]
        self.step -= 1
        self.stepSignal.emit()

        if self.hit_the_wall(newRow,newColumn):
            self.msgSignal.emit('禁止行走！')
        else:
            self.row, self.column = newRow, newColumn
            self.msgSignal.emit(f'往{where}走了一格')

        if self.reach_end(self.row, self.column):
            self.msgSignal.emit('到达终点，成功！')
            return 0

        if self.should_punish(self.row, self.column):
            self.tolerance -= 1
            self.msgSignal.emit(f'你被惩罚了，惩罚次数剩余{self.tolerance}')
            self.punishSignal.emit()

        if not self.can_punish():
            self.msgSignal.emit('无法再被惩罚，失败！')
            return 1

        if self.have_step():
            self.msgSignal.emit(f'还能走{self.step}步.')
        else:
            self.msgSignal.emit('无法继续行走，失败！')
            return 2
        return 3

    # 自动探路一次
    # @1规定——如果在一次行走的过程中，出现任何终止情况，本轮所有规划路径全部作废
    # @2要是没走完路径，也视为作废，需要回到起重新开始
    def autoMoveOnce(
        self,
        path: List[str],
        update_location_func: Callable,  # 更新位置的函数
        break_cope_func: Callable  # 当终止的时候，触发的处理函数
    ) -> None:
        self.timer.start()
        self.timer.timeout.connect(lambda :self._autoMoveStep(path ,update_location_func, break_cope_func))

    def _autoMoveStep(self, path: List[str], update_location_func: Callable, break_cope_func: Callable) -> None:
        if path:
            direction = path[0]
            result = self.move(direction)
            update_location_func()

            if result != 3:
                self.timer.stop()
                break_cope_func()
                path.clear()  # 清空路径
                self.msgSignal.emit('因终止此次自动寻路结束！')
            else:
                path.pop(0)
                print(path)
                if not path:
                    self.timer.stop()
                    # @2
                    break_cope_func()
                    self.msgSignal.emit('因路段不足此次自动寻路结束！')

    # 多次探路
    def autoMove(
            self,
            paths: List[List[str]],
            update_location_func: Callable,
            break_cope_func: Callable
    ) -> None:
        # 定义一个内部函数来处理每条路径
        def process_next_path(path_index: int) -> None:
            if path_index < len(paths):  # 检查是否还有路径
                path = paths[path_index]
                self.autoMoveOnce(
                    path,
                    update_location_func,
                    lambda: (break_cope_func(), process_next_path(path_index + 1))  # 当路径结束时继续下一个路径
                )
            else:
                self.msgSignal.emit('所有路径处理完毕！')  # 所有路径完成的消息

        process_next_path(0)  # 从第一条路径开始处理

    # 抽象策略接口
    def autoPolicy(self, *args, **kwargs):
        pass

# 模拟场景
class Scene(QGraphicsScene, ResetMixin):
    def __init__(self, sceneSize: QSize, walker: Walker, **kwargs):
        super().__init__(**kwargs)
        self.sceneSize = sceneSize
        self.walker = walker
        self.cellWidth, self.cellHeight = self.sceneSize.width() / Column, self.sceneSize.height() / Row
        self.walkerItem: QGraphicsRectItem = self.buildScene()
        self.update_scence_by_walker()

    # 重重置
    def reset(self) -> None:
        self.walker.reset()
        self.update_scence_by_walker()

    # 场景建立
    def buildScene(self) -> QGraphicsRectItem:
        self.clear()
        for r in range(Row):
            for c in range(Column):
                rect = QGraphicsRectItem(c * self.cellWidth, r * self.cellHeight, self.cellWidth, self.cellHeight)
                rect.setBrush(CellColors[Worlds[r][c]])
                self.addItem(rect)
        self.walkerItem = QGraphicsRectItem(QRectF(0, 0, self.cellWidth, self.cellHeight))
        self.walkerItem.setBrush(CellColors[5])
        self.addItem(self.walkerItem)
        return self.walkerItem

    # 更新每次移动Walker后的场景
    def update_scence_by_walker(self) -> None:
        self.walkerItem.setPos(self.walker.column * self.cellWidth, self.walker.row * self.cellHeight)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        keyValue = event.key()
        if keyValue in EventKeys.keys():
            self.walker.move(EventKeys[keyValue])
            self.update_scence_by_walker()
            super().keyPressEvent(event)

class ScoreBoard(QWidget, ResetMixin):
    def __init__(self, step : int, tolerance : int, **kwargs):
        super().__init__(**kwargs)
        self.setMaximumWidth(300)
        self.setStyleSheet('background-color : lightskyblue;')

        self.customMoveBtn = QPushButton('自定义走路')  # 根据自定义策略自动走路
        self.autoFindBtn = QPushButton('自训练寻路')  # 在多次训练配合多次可视化自动寻路

        self.vbox = QVBoxLayout()
        self.hbox1 = QHBoxLayout()
        self.hbox2 = QHBoxLayout()
        self.hbox3 = QHBoxLayout()
        self.hbox4 = QHBoxLayout()
        self.hbox5 = QHBoxLayout()
        self.vbox.addLayout(self.hbox1)
        self.vbox.addLayout(self.hbox2)
        self.vbox.addLayout(self.hbox3)
        self.vbox.addLayout(self.hbox4)
        self.vbox.addLayout(self.hbox5)
        self.setLayout(self.vbox)

        self.stepLCD = QLCDNumber()
        self.leftStepLCD = QLCDNumber()
        self.toleLCD = QLCDNumber()
        self.leftToleLCD = QLCDNumber()

        self.hbox1.addWidget(QLabel('已走步数'))
        self.hbox1.addWidget(self.stepLCD)
        self.hbox2.addWidget(QLabel('剩余步数'))
        self.hbox2.addWidget(self.leftStepLCD)
        self.hbox3.addWidget(QLabel('已被惩罚'))
        self.hbox3.addWidget(self.toleLCD)
        self.hbox4.addWidget(QLabel('剩余惩罚'))
        self.hbox4.addWidget(self.leftToleLCD)

        self.hbox5.addWidget(self.customMoveBtn)
        self.hbox5.addWidget(self.autoFindBtn)

        self.leftStepLCD.display(0)
        self.leftToleLCD.display(tolerance)

        self.init_info_backup = dict(
            step=step,
            tolerance=tolerance
        )

    # 重置
    def reset(self) -> None:
        self.leftStepLCD.display(self.init_info_backup.get('step'))
        self.stepLCD.display(0)
        self.toleLCD.display(0)
        self.leftToleLCD.display(self.init_info_backup.get('tolerance'))

# 界面
class AppCore(QMainWindow, ResetMixin):
    def __init__(self,
                 size : QSize = QSize(800, 600), /, *,
                 sceneSize : QSize,
                 start : List[int], tolerance : int, step : int,
         **kwargs):
        super().__init__(**kwargs)
        self.setMinimumSize(size)

        self.scene = Scene(sceneSize, Walker(start, tolerance, step))
        self.sceneview = QGraphicsView(self.scene)
        self.scoreboard = ScoreBoard(step, tolerance)
        self.msgshower = MsgBox()

        self.__setUI()

    # 初始化
    def __setUI(self) -> None:
        verSplitter = QSplitter()
        horSplitter = QSplitter()
        self.setCentralWidget(verSplitter)

        verSplitter.addWidget(horSplitter)
        verSplitter.addWidget(self.msgshower)
        horSplitter.addWidget(self.sceneview)
        horSplitter.addWidget(self.scoreboard)
        verSplitter.setOrientation(Qt.Vertical)
        horSplitter.setOrientation(Qt.Horizontal)

        self.scene.walker.msgSignal.connect(self.accept_msg)
        self.scene.walker.stepSignal.connect(lambda : self.record_step(True))
        self.scene.walker.punishSignal.connect(lambda: self.record_step(False))

        # 连接自动按钮
        self.scoreboard.customMoveBtn.clicked.connect(lambda : self.autoMove(
            [list('drrdd'), list('drrrdddr'), list('drdrdll')]
        ))

    # 记录面板
    def record_step(self, step : bool):
        if step:
            self.scoreboard.leftStepLCD.display(self.scene.walker.step)
            self.scoreboard.stepLCD.display(self.scene.walker.init_info_backup.get('step') - self.scene.walker.step)
        else:
            self.scoreboard.leftToleLCD.display(self.scene.walker.tolerance)
            self.scoreboard.toleLCD.display(
                self.scene.walker.init_info_backup.get('tolerance') - self.scene.walker.tolerance
            )

        # 接受信息

    def accept_msg(self, msg: str) -> None:
        self.msgshower.appendPlainText(msg)

        if msg == '到达终点，成功！':
            self.msgshower.appendPlainText(
                '-------------------------------------------------------------------------------------\n'
                                           '因成功，新的一轮开始！')
            self.reset()
        elif msg == '无法再被惩罚，失败！' or msg == '无法继续行走，失败！':
            self.msgshower.appendPlainText(
                '-------------------------------------------------------------------------------------\n'
                                           '因失败，新的一轮开始！')
            self.reset()
        elif msg == '因终止此次自动寻路结束！' or msg == '因路段不足此次自动寻路结束！':
            self.msgshower.appendPlainText(
                '-------------------------------------------------------------------------------------\n'
                '自动寻路，新的一轮开始！')
            # 这里针对自动寻路，自动寻路已经传入了重置方法，不用再重置
        else:
            pass

    # 重置
    def reset(self):
        self.scoreboard.reset()
        self.scene.reset()

    # 自动走
    def autoMove(self, path : Union[List[List[str]], List[str]]) -> None:
        if isinstance(path[0], str):
            self.scene.walker.autoMoveOnce(
                path,
                self.scene.update_scence_by_walker,
                self.reset
            )
        else:
            self.scene.walker.autoMove(
                path,
                self.scene.update_scence_by_walker,
                self.reset
            )

def main(
        size: QSize = QSize(800, 600), /, *,
        sceneSize: QSize,
        start: List[int], tolerance: int, step: int,
):
    app = QApplication([])
    app.setApplicationDisplayName('GridWorld')
    ui = AppCore(size, sceneSize=sceneSize, start=start, tolerance=tolerance, step=step)
    ui.setStyleSheet(open('style.css').read())
    ui.show()
    app.exec()

if __name__ == '__main__':
    main(
        QSize(1200, 800),
        sceneSize=QSize(800, 600),
        start=GlobalMapSettings.get('start'),
        tolerance=10,
        step=20
    )