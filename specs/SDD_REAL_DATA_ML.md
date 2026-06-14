# 软件设计规格说明 (SDD)
# 真实数据接入和机器学习模块

---

## 文档信息

| 项目 | 内容 |
|------|------|
| 文档名称 | 真实数据接入和机器学习模块 SDD |
| 版本 | v1.0 |
| 创建日期 | 2026-06-14 |
| 状态 | 待实现 |

---

## 1. 引言

### 1.1 目的

本文档详细描述真实数据接入和机器学习模块的设计规格，将模拟数据替换为真实数据，并引入 ML 模型优化推荐算法。

### 1.2 范围

本阶段负责：
- 真实基本面数据接入
- 机器学习推荐模型
- 特征工程
- 模型训练和预测

---

## 2. 真实数据接入设计

### 2.1 数据源

| 数据类型 | akshare 函数 | 返回内容 |
|---------|-------------|---------|
| 财务指标 | stock_financial_analysis_indicator | ROE/ROA/毛利率等 |
| 财务摘要 | stock_financial_abstract | 综合财务数据 |
| 成长能力 | stock_zh_growth_comparison_em | 增长率对比 |
| 股票历史 | stock_zh_a_hist | 历史行情数据 |

### 2.2 核心接口

```python
class RealDataProvider:
    """真实数据提供器"""

    def get_financial_indicators(self, stock_code: str) -> dict:
        """获取财务指标"""
        pass

    def get_financial_abstract(self, stock_code: str) -> pd.DataFrame:
        """获取财务摘要"""
        pass

    def get_growth_data(self, stock_code: str) -> dict:
        """获取成长数据"""
        pass
```

---

## 3. 机器学习模块设计

### 3.1 特征工程

| 特征类别 | 特征 | 说明 |
|---------|------|------|
| 估值特征 | PE、PB、PS | 市盈率/市净率/市销率 |
| 盈利特征 | ROE、ROA、毛利率 | 盈利能力 |
| 成长特征 | 营收增长、利润增长 | 成长能力 |
| 技术特征 | MA、RSI、MACD | 技术指标 |
| 市场特征 | 板块涨跌、北向资金 | 市场情绪 |

### 3.2 模型选择

| 模型 | 用途 | 优势 |
|------|------|------|
| Random Forest | 分类/回归 | 稳定、可解释 |
| XGBoost | 分类/回归 | 准确率高 |
| LightGBM | 分类/回归 | 训练速度快 |

### 3.3 核心接口

```python
class MLRecommender:
    """机器学习推荐器"""

    def prepare_features(self, stock_codes: list) -> pd.DataFrame:
        """准备特征"""
        pass

    def train(self, X: pd.DataFrame, y: pd.Series):
        """训练模型"""
        pass

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """预测"""
        pass

    def recommend(self, top_n: int = 10) -> list:
        """推荐股票"""
        pass
```

---

## 4. 实现检查清单

### 4.1 真实数据接入

- [ ] 实现 RealDataProvider
- [ ] 实现财务指标获取
- [ ] 实现财务摘要获取
- [ ] 实现数据缓存

### 4.2 机器学习模块

- [ ] 实现特征工程
- [ ] 实现 MLRecommender
- [ ] 实现模型训练
- [ ] 实现模型预测

---

## 5. 交付物清单

| 交付物 | 文件路径 | 状态 |
|--------|---------|------|
| 真实数据提供器 | core/data/real_provider.py | ⬜ |
| 机器学习推荐器 | skills/stock-recommender/ml_recommender.py | ⬜ |
| 单元测试 | tests/test_real_data_ml.py | ⬜ |

---

## 6. 变更记录

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|---------|------|
| v1.0 | 2026-06-14 | 初始版本 | - |
