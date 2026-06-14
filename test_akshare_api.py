#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试 akshare 基本面数据接口"""

import akshare as ak

print("=" * 60)
print("akshare 基本面数据接口测试")
print("=" * 60)

# 测试1: 财务分析指标
print("\n1. 测试 stock_financial_analysis_indicator...")
try:
    df = ak.stock_financial_analysis_indicator(symbol='000001', start_year='2023')
    print(f"   获取到 {len(df)} 条数据")
    print(f"   列名: {df.columns.tolist()[:10]}")
    print(f"   最新数据:")
    print(df.head(1).to_string())
except Exception as e:
    print(f"   失败: {e}")

# 测试2: 财务摘要
print("\n2. 测试 stock_financial_abstract...")
try:
    df = ak.stock_financial_abstract(symbol='000001')
    print(f"   获取到 {len(df)} 条数据")
    print(f"   列名: {df.columns.tolist()[:10]}")
except Exception as e:
    print(f"   失败: {e}")

# 测试3: 利润表
print("\n3. 测试 stock_profit_sheet_by_report_em...")
try:
    df = ak.stock_profit_sheet_by_report_em(symbol='000001')
    print(f"   获取到 {len(df)} 条数据")
    print(f"   列名: {df.columns.tolist()[:10]}")
except Exception as e:
    print(f"   失败: {e}")

# 测试4: 资产负债表
print("\n4. 测试 stock_balance_sheet_by_report_em...")
try:
    df = ak.stock_balance_sheet_by_report_em(symbol='000001')
    print(f"   获取到 {len(df)} 条数据")
    print(f"   列名: {df.columns.tolist()[:10]}")
except Exception as e:
    print(f"   失败: {e}")

# 测试5: 成长能力对比
print("\n5. 测试 stock_zh_growth_comparison_em...")
try:
    df = ak.stock_zh_growth_comparison_em(symbol='000001')
    print(f"   获取到 {len(df)} 条数据")
    print(f"   列名: {df.columns.tolist()[:10]}")
except Exception as e:
    print(f"   失败: {e}")

print("\n" + "=" * 60)
print("测试完成！")
print("=" * 60)
