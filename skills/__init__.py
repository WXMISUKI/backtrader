# Skills 模块
"""
Skills 目录包含所有可插拔的功能模块
每个 Skill 都是一个独立的功能单元

可用的 Skills:
- stock_advisor: 个股买卖建议
"""

# 延迟导入，避免循环依赖
def get_stock_advisor():
    """获取 Stock Advisor Skill"""
    from .stock_advisor import StockAnalyzer, analyze, batch_analyze
    return {
        'StockAnalyzer': StockAnalyzer,
        'analyze': analyze,
        'batch_analyze': batch_analyze
    }

__all__ = ['get_stock_advisor']
