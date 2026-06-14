#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Stock Advisor Skill - 个股买卖建议

提供完整的股票分析功能:
- 数据获取和技术指标计算
- 买卖信号生成
- 风险评估
- 投资建议

使用示例:
    # 简单用法
    from skills.stock_advisor import analyze
    result = analyze("000001")
    print(result.summary())

    # 高级用法
    from skills.stock_advisor import StockAnalyzer, AnalysisConfig
    config = AnalysisConfig(risk_profile="aggressive")
    analyzer = StockAnalyzer(config)
    result = analyzer.analyze("000001")
"""

from .stock_data import StockData
from .analyzer import (
    StockAnalyzer,
    AnalysisConfig,
    AnalysisResult,
    RiskAssessment,
    Recommendation,
    analyze,
    batch_analyze
)

# 模块版本
__version__ = '1.0.0'

# 导出所有公共接口
__all__ = [
    # 核心类
    'StockData',
    'StockAnalyzer',

    # 配置和结果类
    'AnalysisConfig',
    'AnalysisResult',
    'RiskAssessment',
    'Recommendation',

    # 便捷函数
    'analyze',
    'batch_analyze',
]
