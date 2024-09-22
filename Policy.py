from typing import *
from abc import ABC, abstractmethod

# 抽象的强化策略接口
class AbstractPolicy(ABC):
    # 反馈函数，根据自己的目标做反馈。例如我定义一个 步数 / 惩罚 为权衡系数，我的反馈函数就可以返回这个值
    @abstractmethod
    def feedback(self, *args, **kwargs) -> Any:
        pass

    # 决策函数，得到最优策略
    @abstractmethod
    def decide(self, *args, **kwargs) -> Any:
        pass

    # 优化目标函数，使用来不断调整你的策略
    @abstractmethod
    def optimal(self, *args, **kwargs) -> Any:
        pass

    # 最优路径，是由决策函数得到的
    @abstractmethod
    def optimal_path(self) -> List[str]:
        pass

    # 策略学习，每次得到一个路径，会触发反馈函数
    @abstractmethod
    def policy_learing(self, *args, **kwargs) -> List[str]:
        pass
