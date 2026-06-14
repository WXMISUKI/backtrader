#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
报告生成器

生成格式化的分析报告

支持的报告类型:
- 个股分析报告
- 回测报告
- 选股报告
"""

import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import asdict


class ReportGenerator:
    """
    报告生成器

    生成格式化的分析报告

    示例:
        >>> from skills.stock_report import ReportGenerator
        >>> report = ReportGenerator.generate_stock_report(result)
        >>> print(report)
    """

    @staticmethod
    def generate_stock_report(analysis_result) -> str:
        """
        生成个股分析报告

        参数:
            analysis_result: AnalysisResult 对象

        返回:
            格式化的报告字符串
        """
        r = analysis_result
        s = r.stock_data

        action_map = {
            'BUY': '📈 买入',
            'SELL': '📉 卖出',
            'HOLD': '⏸️ 观望'
        }

        report = f"""
{'='*60}
                    个股分析报告
{'='*60}

【基本信息】
股票代码: {s.code}
股票名称: {s.name}
当前价格: {s.latest_price:.2f}
数据区间: {s.date_range[0].strftime('%Y-%m-%d')} ~ {s.date_range[1].strftime('%Y-%m-%d')}

{'─'*60}
【技术指标】
5日均线: {s.indicators.get('ma5', pd.Series()).iloc[-1]:.2f}
10日均线: {s.indicators.get('ma10', pd.Series()).iloc[-1]:.2f}
20日均线: {s.indicators.get('ma20', pd.Series()).iloc[-1]:.2f}
RSI(14): {s.indicators.get('rsi', pd.Series()).iloc[-1]:.2f}
MACD DIF: {s.indicators.get('macd_dif', pd.Series()).iloc[-1]:.4f}
MACD DEA: {s.indicators.get('macd_dea', pd.Series()).iloc[-1]:.4f}

{'─'*60}
【交易信号】
信号方向: {action_map.get(r.signal.get('direction', 'HOLD'), '⏸️ 观望')}
买入强度: {r.signal.get('buy_strength', 0):.2%}
卖出强度: {r.signal.get('sell_strength', 0):.2%}
置信度: {r.signal.get('confidence', 0):.2%}

{'─'*60}
【风险评估】
波动率: {r.risk.volatility:.2%}
最大回撤: {r.risk.max_drawdown:.2%}
风险等级: {r.risk.risk_level}

{'─'*60}
【投资建议】
操作建议: {action_map.get(r.recommendation.action, '⏸️ 观望')}
建议原因: {r.recommendation.reason}
目标价格: {r.recommendation.target_price:.2f}
止损价格: {r.recommendation.stop_loss:.2f}
建议仓位: {r.recommendation.position_ratio:.0%}

{'='*60}
⚠️ 免责声明: 以上分析仅供参考，不构成投资建议。
   投资有风险，入市需谨慎。
{'='*60}
"""
        return report

    @staticmethod
    def generate_backtest_report(backtest_result) -> str:
        """
        生成回测报告

        参数:
            backtest_result: BacktestResult 对象

        返回:
            格式化的报告字符串
        """
        r = backtest_result

        report = f"""
{'='*60}
                    回测报告
{'='*60}

【基本信息】
股票代码: {r.stock_code}
策略名称: {r.strategy_name}
回测区间: {r.start_date} ~ {r.end_date}

{'─'*60}
【资金信息】
初始资金: {r.initial_cash:,.2f}
最终资金: {r.final_value:,.2f}
总收益率: {r.total_return:.2%}
年化收益: {r.annual_return:.2%}

{'─'*60}
【风险指标】
最大回撤: {r.max_drawdown:.2%}
夏普比率: {r.sharpe_ratio:.2f}
波动率: {r.volatility:.2%}

{'─'*60}
【交易统计】
总交易数: {r.total_trades}
盈利次数: {r.winning_trades}
亏损次数: {r.losing_trades}
胜率: {r.win_rate:.2%}
平均盈利: {r.avg_profit:.2f}
平均亏损: {r.avg_loss:.2f}
盈亏比: {r.profit_factor:.2f}

{'='*60}
"""
        return report

    @staticmethod
    def generate_screening_report(candidates: list) -> str:
        """
        生成选股报告

        参数:
            candidates: StockCandidate 列表

        返回:
            格式化的报告字符串
        """
        report = f"""
{'='*60}
                    智能选股报告
{'='*60}

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
筛选结果: {len(candidates)} 只股票

{'─'*60}
【候选股票】
"""

        for i, stock in enumerate(candidates, 1):
            signals_str = ', '.join(stock.signals) if stock.signals else '无'
            report += f"""
{i}. {stock.name}({stock.code})
   当前价格: {stock.price:.2f}
   触发信号: {signals_str}
   综合得分: {stock.score:.2f}
"""

        report += f"""
{'='*60}
⚠️ 免责声明: 以上筛选结果仅供参考，不构成投资建议。
{'='*60}
"""
        return report

    @staticmethod
    def generate_json_report(data: dict) -> str:
        """
        生成 JSON 报告

        参数:
            data: 报告数据

        返回:
            JSON 字符串
        """
        return json.dumps(data, indent=2, ensure_ascii=False, default=str)


# 便捷函数
def generate_stock_report(analysis_result) -> str:
    """生成个股分析报告"""
    return ReportGenerator.generate_stock_report(analysis_result)


def generate_backtest_report(backtest_result) -> str:
    """生成回测报告"""
    return ReportGenerator.generate_backtest_report(backtest_result)


def generate_screening_report(candidates: list) -> str:
    """生成选股报告"""
    return ReportGenerator.generate_screening_report(candidates)


# 测试代码
if __name__ == "__main__":
    print("=" * 60)
    print("报告生成器测试")
    print("=" * 60)

    # 测试 JSON 报告
    print("\n1. JSON 报告测试:")
    data = {
        'stock_code': '000001',
        'stock_name': '平安银行',
        'price': 11.24,
        'signal': 'BUY'
    }
    json_report = ReportGenerator.generate_json_report(data)
    print(json_report)

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
