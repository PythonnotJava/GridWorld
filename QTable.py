# 计算Q表格的方法
from typing import *

import numpy

from GlobalSetting import *


# 返回的是每个格子到上下左右格子的得分（可能会正常走、可能是起点（比正常走得分少）、可能是禁行区域、可能是惩罚但是可以走、可能是终点）
# 传入参数是网格世界的行列数、网格世界组成
def getQTable(row: int, column: int) -> numpy.ndarray:
    array = numpy.zeros(shape=[row, column, 4])

    for r in range(row):
        for c in range(column):
            # 上
            if r > 0 and Worlds[r - 1][c] != 2:  # 禁行区
                array[r][c][0] = RewordsMap[Worlds[r - 1][c]]
            else:
                array[r][c][0] = -float('inf')  # 碰壁或禁行区

            # 下
            if r < row - 1 and Worlds[r + 1][c] != 2:  # 禁行区
                array[r][c][1] = RewordsMap[Worlds[r + 1][c]]
            else:
                array[r][c][1] = -float('inf')  # 碰壁或禁行区

            # 左
            if c > 0 and Worlds[r][c - 1] != 2:  # 禁行区
                array[r][c][2] = RewordsMap[Worlds[r][c - 1]]
            else:
                array[r][c][2] = -float('inf')  # 碰壁或禁行区

            # 右
            if c < column - 1 and Worlds[r][c + 1] != 2:  # 禁行区
                array[r][c][3] = RewordsMap[Worlds[r][c + 1]]
            else:
                array[r][c][3] = -float('inf')  # 碰壁或禁行区

    return array

if __name__ == '__main__':
    # 获取 Q 表
    q_table = getQTable(len(Worlds), len(Worlds[0]))
    print(q_table)