#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
策略注册表

借鉴 vectorbt 的指标工厂模式
支持策略注册、查询、实例化

示例:
    @StrategyRegistry.register("ma_cross")
    class MACrossStrategy(Strategy):
        pass

    strategy = StrategyRegistry.create("ma_cross", config)
"""

from typing import Dict, Type, List, Optional, Any
from .base import Strategy


class StrategyRegistry:
    """
    策略注册表

    管理所有可用策略的注册和实例化

    示例:
        # 注册策略
        @StrategyRegistry.register("ma_cross")
        class MACrossStrategy(Strategy):
            pass

        # 创建策略实例
        strategy = StrategyRegistry.create("ma_cross", {'fast': 5, 'slow': 20})

        # 列出所有策略
        print(StrategyRegistry.list())
    """

    _strategies: Dict[str, Type[Strategy]] = {}

    @classmethod
    def register(cls, name: str = None):
        """
        注册策略装饰器

        参数:
            name: 策略名称，默认使用类名

        返回:
            装饰器函数

        示例:
            @StrategyRegistry.register("ma_cross")
            class MACrossStrategy(Strategy):
                pass
        """
        def decorator(strategy_cls: Type[Strategy]) -> Type[Strategy]:
            # 验证是否是 Strategy 的子类
            if not issubclass(strategy_cls, Strategy):
                raise TypeError(
                    f"{strategy_cls.__name__} 必须是 Strategy 的子类"
                )

            strategy_name = name or strategy_cls.__name__
            cls._strategies[strategy_name] = strategy_cls
            return strategy_cls

        return decorator

    @classmethod
    def get(cls, name: str) -> Type[Strategy]:
        """
        获取策略类

        参数:
            name: 策略名称

        返回:
            策略类

        异常:
            KeyError: 策略不存在
        """
        if name not in cls._strategies:
            available = cls.list()
            raise KeyError(
                f"未找到策略: '{name}'，可用策略: {available}"
            )
        return cls._strategies[name]

    @classmethod
    def create(cls, name: str, config: Dict[str, Any] = None) -> Strategy:
        """
        创建策略实例

        参数:
            name: 策略名称
            config: 策略配置

        返回:
            策略实例

        示例:
            strategy = StrategyRegistry.create("ma_cross", {
                'fast_period': 5,
                'slow_period': 20
            })
        """
        strategy_cls = cls.get(name)
        return strategy_cls(config)

    @classmethod
    def list(cls) -> List[str]:
        """
        列出所有已注册的策略

        返回:
            策略名称列表
        """
        return list(cls._strategies.keys())

    @classmethod
    def exists(cls, name: str) -> bool:
        """
        检查策略是否存在

        参数:
            name: 策略名称

        返回:
            是否存在
        """
        return name in cls._strategies

    @classmethod
    def clear(cls):
        """清除所有注册"""
        cls._strategies.clear()

    @classmethod
    def get_info(cls, name: str) -> dict:
        """
        获取策略信息

        参数:
            name: 策略名称

        返回:
            策略信息字典
        """
        strategy_cls = cls.get(name)
        return {
            'name': name,
            'class': strategy_cls.__name__,
            'module': strategy_cls.__module__,
            'description': strategy_cls.__doc__ or "",
            'config_keys': list(strategy_cls({}).config.keys()) if hasattr(strategy_cls({}), 'config') else []
        }

    @classmethod
    def get_all_info(cls) -> List[dict]:
        """
        获取所有策略信息

        返回:
            策略信息列表
        """
        return [cls.get_info(name) for name in cls.list()]


# 便捷函数
def register_strategy(name: str = None):
    """
    注册策略的便捷函数

    示例:
        @register_strategy("ma_cross")
        class MACrossStrategy(Strategy):
            pass
    """
    return StrategyRegistry.register(name)


def get_strategy(name: str, config: Dict[str, Any] = None) -> Strategy:
    """
    获取策略实例的便捷函数

    示例:
        strategy = get_strategy("ma_cross", {'fast': 5, 'slow': 20})
    """
    return StrategyRegistry.create(name, config)


def list_strategies() -> List[str]:
    """
    列出所有策略的便捷函数

    示例:
        strategies = list_strategies()
    """
    return StrategyRegistry.list()


# 测试代码
if __name__ == "__main__":
    print("=" * 60)
    print("策略注册表测试")
    print("=" * 60)

    # 清除之前的注册
    StrategyRegistry.clear()

    # 测试注册
    print("\n1. 注册策略:")
    @StrategyRegistry.register("test_strategy")
    class TestStrategy(Strategy):
        """测试策略"""
        def on_bar(self, bar):
            return None

    print(f"   已注册策略: {StrategyRegistry.list()}")

    # 测试创建实例
    print("\n2. 创建实例:")
    strategy = StrategyRegistry.create("test_strategy", {'param1': 1})
    print(f"   策略名称: {strategy.name}")
    print(f"   策略配置: {strategy.config}")

    # 测试获取信息
    print("\n3. 策略信息:")
    info = StrategyRegistry.get_info("test_strategy")
    print(f"   {info}")

    # 测试异常
    print("\n4. 异常测试:")
    try:
        StrategyRegistry.get("nonexistent")
    except KeyError as e:
        print(f"   KeyError: {e}")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
