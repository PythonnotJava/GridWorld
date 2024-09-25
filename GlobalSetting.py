import json
from typing import *
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt

"""
规定：
    - 区域布局是锁死的
    - 惩罚后容忍值达到0就结束
    - 模拟者先走再判断
"""

GlobalMapSettings = json.load(open('maps.json', 'r'))

# 不同作用的单元格的颜色配置
CellColors = {
    0 : QColor('white'),  # 可通行
    1 : QColor('yellow'),  # 可通行但惩罚区
    2 : QColor('grey'),  # 禁行区
    3 : QColor('blue'),  # 起点
    4 : QColor('#000000'),  # 终点
    5 : QColor('red'),  # 模拟单元
}

# 行走方向的方式，左右上下
MoveDirections = {
    'l' : [[0, -1], '👈'],
    'r' : [[0, 1], '👉'],
    'u' : [[-1, 0], '👆'],
    'd' : [[1, 0], '👇']
}

EventKeys = {
    Qt.Key_Up : 'u',
    Qt.Key_Down : 'd',
    Qt.Key_Left : 'l',
    Qt.Key_Right : 'r'
}

# 网格世界
Worlds : List[List[int]] = GlobalMapSettings.get('grids')
Row, Column = GlobalMapSettings.get('shape')

# 每秒行走格子数
Speed = 8

Inf = float('inf')

# 奖励机制
RewordsMap = {
    0 : 1.0,
    1 : 0.5,
    2: -Inf,
    3 : 0.5,
    4 : 100,
}



if __name__ == '__main__':
    print((-float('inf')) ** 2)