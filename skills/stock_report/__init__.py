#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
报告生成 Skill

生成格式化的分析报告

使用示例:
    from skills.stock_report import ReportGenerator
    report = ReportGenerator.generate_stock_report(result)
"""

from .generator import (
    ReportGenerator,
    generate_stock_report,
    generate_backtest_report,
    generate_screening_report
)

__version__ = '1.0.0'

__all__ = [
    'ReportGenerator',
    'generate_stock_report',
    'generate_backtest_report',
    'generate_screening_report',
]
