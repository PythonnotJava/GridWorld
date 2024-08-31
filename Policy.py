from typing import *
from abc import ABC, abstractmethod

from PyQt5.QtCore import QObject

from GridWorld import Walker
class AbstractPolicy(QObject, metaclass=ABC):
    # walk函数控制人物的行走
    @abstractmethod
    def walk(self) -> None: pass
    # train函数用于训练人物寻求最优解
    @abstractmethod
    def train(self) -> None: pass
    # feedback函数对每次训练结果一个反馈
    @abstractmethod
    def feedback(self) -> None: pass
    # callback函数对最后一次或者找到最优训练后对总体程序的反馈
    @abstractmethod
    def callback(self) -> None: pass


