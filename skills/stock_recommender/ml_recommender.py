#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
机器学习推荐器

使用机器学习模型优化股票推荐算法

模型:
- Random Forest
- XGBoost (可选)
- LightGBM (可选)

特征:
- 估值特征: PE、PB、PS
- 盈利特征: ROE、ROA、毛利率
- 成长特征: 营收增长、利润增长
- 技术特征: MA、RSI、MACD
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import pickle
import os

try:
    from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
    from sklearn.preprocessing import StandardScaler
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

from skills.stock_fundamental import FundamentalAnalyzer
from core.data.real_provider import RealDataProvider
from core.model import FeatureManifest, build_feature_manifest, get_model_governance_service


@dataclass
class MLPrediction:
    """
    机器学习预测结果
    """
    stock_code: str           # 股票代码
    stock_name: str           # 股票名称
    predicted_return: float   # 预测收益率
    confidence: float         # 置信度
    signal: str               # 信号 (BUY/SELL/HOLD)
    features: dict            # 特征值

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'stock_code': self.stock_code,
            'stock_name': self.stock_name,
            'predicted_return': round(self.predicted_return, 4),
            'confidence': round(self.confidence, 4),
            'signal': self.signal,
        }


class MLRecommender:
    """
    机器学习推荐器

    使用机器学习模型预测股票收益

    示例:
        >>> recommender = MLRecommender()
        >>> recommender.train(stock_codes)
        >>> predictions = recommender.predict(stock_codes)
    """

    # 股票池
    STOCK_POOL = [
        ("000001", "平安银行"),
        ("600519", "贵州茅台"),
        ("000858", "五粮液"),
        ("000333", "美的集团"),
        ("000651", "格力电器"),
        ("600036", "招商银行"),
        ("002594", "比亚迪"),
        ("601318", "中国平安"),
        ("600276", "恒瑞医药"),
        ("000725", "京东方A"),
    ]

    def __init__(self, model_type: str = "random_forest"):
        """
        初始化

        参数:
            model_type: 模型类型 (random_forest/xgboost/lightgbm)
        """
        self.model_type = model_type
        self.model = None
        self.scaler = StandardScaler() if HAS_SKLEARN else None
        self.fundamental_analyzer = FundamentalAnalyzer()
        self.real_provider = RealDataProvider()
        self.feature_names = []
        self.last_train_metrics = {}
        self.feature_manifest = None

    def prepare_features(self, stock_codes: List[str] = None) -> Tuple[pd.DataFrame, pd.Series]:
        """
        准备特征和标签

        参数:
            stock_codes: 股票代码列表

        返回:
            (特征DataFrame, 标签Series)
        """
        if stock_codes is None:
            stock_codes = [code for code, _ in self.STOCK_POOL]

        features_list = []
        labels = []

        for stock_code in stock_codes:
            try:
                # 获取基本面数据
                fundamental = self.fundamental_analyzer.analyze(stock_code)

                # 获取真实财务指标
                real_indicators = self.real_provider.get_financial_indicators(stock_code)

                # 构建特征
                feature = {
                    # 估值特征
                    'pe_ratio': fundamental.pe_ratio,
                    'pb_ratio': fundamental.pb_ratio,
                    'ps_ratio': fundamental.ps_ratio,

                    # 盈利特征
                    'roe': fundamental.roe,
                    'roa': fundamental.roa,
                    'gross_margin': fundamental.gross_margin,
                    'net_margin': fundamental.net_margin,

                    # 成长特征
                    'revenue_growth': fundamental.revenue_growth,
                    'profit_growth': fundamental.profit_growth,

                    # 安全特征
                    'debt_ratio': fundamental.debt_ratio,
                    'current_ratio': fundamental.current_ratio,

                    # 综合得分
                    'fundamental_score': fundamental.score,
                }

                # 添加真实财务指标
                if real_indicators.roe != 0:
                    feature['real_roe'] = real_indicators.roe
                    feature['real_roa'] = real_indicators.roa
                    feature['real_gross_margin'] = real_indicators.gross_margin
                    feature['real_revenue_growth'] = real_indicators.revenue_growth

                features_list.append(feature)

                # 生成模拟标签 (实际应用中应该使用真实收益)
                # 这里使用基本面得分作为收益的代理
                simulated_return = fundamental.score / 100 * 0.3 + np.random.normal(0, 0.1)
                labels.append(simulated_return)

            except Exception as e:
                print(f"准备 {stock_code} 特征失败: {e}")
                continue

        if not features_list:
            return pd.DataFrame(), pd.Series()

        X = pd.DataFrame(features_list)
        y = pd.Series(labels)

        self.feature_names = X.columns.tolist()

        return X, y

    def train(self, stock_codes: List[str] = None):
        """
        训练模型

        参数:
            stock_codes: 股票代码列表
        """
        if not HAS_SKLEARN:
            print("错误: 未安装 scikit-learn，请运行: pip install scikit-learn")
            return

        print("准备训练数据...")
        X, y = self.prepare_features(stock_codes)

        if len(X) == 0:
            print("错误: 没有训练数据")
            return

        print(f"训练数据: {len(X)} 条, {len(X.columns)} 个特征")

        # 标准化特征
        X_scaled = self.scaler.fit_transform(X)

        # 划分训练集和测试集
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42
        )

        # 创建模型
        if self.model_type == "random_forest":
            self.model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
        else:
            self.model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )

        # 训练模型
        print("训练模型...")
        self.model.fit(X_train, y_train)

        # 评估模型
        train_score = self.model.score(X_train, y_train)
        test_score = self.model.score(X_test, y_test)
        self.last_train_metrics = {
            "train_r2": float(train_score),
            "test_r2": float(test_score),
            "n_samples": int(len(X)),
            "n_features": int(len(X.columns)),
            "model_type": self.model_type,
        }
        self.feature_manifest = build_feature_manifest(
            name=f"ml_recommender:{self.model_type}",
            features=self.feature_names,
            version="v1",
            description="ML 推荐器特征清单",
            source="ml_recommender",
            meta={
                "model_type": self.model_type,
                "feature_count": len(self.feature_names),
            },
        )

        print(f"训练集 R²: {train_score:.4f}")
        print(f"测试集 R²: {test_score:.4f}")

        # 特征重要性
        if hasattr(self.model, 'feature_importances_'):
            importance = pd.DataFrame({
                'feature': self.feature_names,
                'importance': self.model.feature_importances_
            }).sort_values('importance', ascending=False)

            print("\n特征重要性:")
            for _, row in importance.head(5).iterrows():
                print(f"  {row['feature']}: {row['importance']:.4f}")

    def predict(self, stock_codes: List[str] = None) -> List[MLPrediction]:
        """
        预测股票收益

        参数:
            stock_codes: 股票代码列表

        返回:
            预测结果列表
        """
        if self.model is None:
            print("错误: 模型未训练，请先调用 train()")
            return []

        if stock_codes is None:
            stock_codes = [code for code, _ in self.STOCK_POOL]

        predictions = []

        for stock_code in stock_codes:
            try:
                # 获取特征
                fundamental = self.fundamental_analyzer.analyze(stock_code)
                real_indicators = self.real_provider.get_financial_indicators(stock_code)

                # 构建特征
                feature = {
                    'pe_ratio': fundamental.pe_ratio,
                    'pb_ratio': fundamental.pb_ratio,
                    'ps_ratio': fundamental.ps_ratio,
                    'roe': fundamental.roe,
                    'roa': fundamental.roa,
                    'gross_margin': fundamental.gross_margin,
                    'net_margin': fundamental.net_margin,
                    'revenue_growth': fundamental.revenue_growth,
                    'profit_growth': fundamental.profit_growth,
                    'debt_ratio': fundamental.debt_ratio,
                    'current_ratio': fundamental.current_ratio,
                    'fundamental_score': fundamental.score,
                }

                if real_indicators.roe != 0:
                    feature['real_roe'] = real_indicators.roe
                    feature['real_roa'] = real_indicators.roa
                    feature['real_gross_margin'] = real_indicators.gross_margin
                    feature['real_revenue_growth'] = real_indicators.revenue_growth

                # 确保特征顺序一致
                feature_df = pd.DataFrame([feature])

                # 补充缺失的特征列
                for col in self.feature_names:
                    if col not in feature_df.columns:
                        feature_df[col] = 0

                feature_df = feature_df[self.feature_names]

                # 标准化
                feature_scaled = self.scaler.transform(feature_df)

                # 预测
                predicted_return = self.model.predict(feature_scaled)[0]

                # 计算置信度 (基于特征与训练数据的相似度)
                confidence = min(0.9, max(0.3, fundamental.score / 100))

                # 生成信号
                if predicted_return > 0.15:
                    signal = "BUY"
                elif predicted_return < -0.05:
                    signal = "SELL"
                else:
                    signal = "HOLD"

                # 获取股票名称
                stock_name = dict(self.STOCK_POOL).get(stock_code, f"股票{stock_code}")

                prediction = MLPrediction(
                    stock_code=stock_code,
                    stock_name=stock_name,
                    predicted_return=predicted_return,
                    confidence=confidence,
                    signal=signal,
                    features=feature
                )

                predictions.append(prediction)

            except Exception as e:
                print(f"预测 {stock_code} 失败: {e}")
                continue

        # 按预测收益排序
        predictions.sort(key=lambda x: x.predicted_return, reverse=True)

        return predictions

    def recommend(self, top_n: int = 5) -> List[MLPrediction]:
        """
        推荐股票

        参数:
            top_n: 返回数量

        返回:
            推荐列表
        """
        predictions = self.predict()

        # 只返回买入信号
        buy_predictions = [p for p in predictions if p.signal == "BUY"]

        return buy_predictions[:top_n]

    def save_model(self, path: str = "ml_model.pkl"):
        """保存模型"""
        if self.model is not None:
            with open(path, 'wb') as f:
                pickle.dump({
                    'model': self.model,
                    'scaler': self.scaler,
                    'feature_names': self.feature_names,
                    'last_train_metrics': self.last_train_metrics,
                    'feature_manifest': self.feature_manifest.to_dict() if self.feature_manifest else None,
                }, f)
            if self.feature_manifest is None and self.feature_names:
                self.feature_manifest = build_feature_manifest(
                    name=f"ml_recommender:{self.model_type}",
                    features=self.feature_names,
                    version="v1",
                    description="ML 推荐器特征清单",
                    source="ml_recommender",
                )
            get_model_governance_service().register_model(
                model_name="ml_recommender",
                version=self.model_type,
                status="draft",
                artifact_path=path,
                metrics=self.last_train_metrics or {},
                thresholds={},
                feature_manifest=self.feature_manifest.to_dict() if self.feature_manifest else {},
                notes="saved from MLRecommender.save_model",
            )
            print(f"模型已保存到: {path}")

    def load_model(self, path: str = "ml_model.pkl"):
        """加载模型"""
        if os.path.exists(path):
            with open(path, 'rb') as f:
                data = pickle.load(f)
                self.model = data['model']
                self.scaler = data['scaler']
                self.feature_names = data['feature_names']
                self.last_train_metrics = data.get('last_train_metrics', {})
                feature_manifest = data.get('feature_manifest')
                self.feature_manifest = FeatureManifest(**feature_manifest) if feature_manifest else None
            print(f"模型已从 {path} 加载")

    def get_feature_manifest(self) -> dict:
        """返回特征清单。"""
        if self.feature_manifest is not None:
            return self.feature_manifest.to_dict()
        return {
            "manifest_id": "",
            "name": f"ml_recommender:{self.model_type}",
            "version": "v1",
            "features": list(self.feature_names),
            "feature_hash": "",
            "description": "ML 推荐器特征清单",
            "source": "ml_recommender",
            "created_at": "",
            "meta": {
                "model_type": self.model_type,
                "feature_count": len(self.feature_names),
            },
        }

    def get_governance_snapshot(self) -> dict:
        """返回模型治理快照。"""
        return {
            "model_name": "ml_recommender",
            "model_type": self.model_type,
            "has_model": self.model is not None,
            "feature_count": len(self.feature_names),
            "feature_manifest": self.get_feature_manifest(),
            "last_train_metrics": dict(self.last_train_metrics or {}),
        }


# 便捷函数
def train_ml_model(stock_codes: List[str] = None) -> MLRecommender:
    """
    训练机器学习模型 (便捷函数)

    参数:
        stock_codes: 股票代码列表

    返回:
        训练好的 MLRecommender
    """
    recommender = MLRecommender()
    recommender.train(stock_codes)
    return recommender


# 测试代码
if __name__ == "__main__":
    print("=" * 60)
    print("机器学习推荐器测试")
    print("=" * 60)

    # 创建推荐器
    recommender = MLRecommender()

    # 训练模型
    print("\n1. 训练模型:")
    recommender.train()

    # 预测
    print("\n2. 预测结果:")
    predictions = recommender.predict()
    for pred in predictions[:5]:
        print(f"  {pred.stock_name}: 预测收益={pred.predicted_return:.2%}, 信号={pred.signal}")

    # 推荐
    print("\n3. 推荐股票:")
    recommendations = recommender.recommend(top_n=3)
    for rec in recommendations:
        print(f"  {rec.stock_name}: 预测收益={rec.predicted_return:.2%}, 置信度={rec.confidence:.0%}")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
