"""
在线学习器模块
支持模型增量更新和版本管理
"""

import numpy as np
import pickle
import os
import json
from datetime import datetime
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, asdict


@dataclass
class ModelVersion:
    """模型版本信息"""
    version: int
    timestamp: str
    n_samples: int
    metrics: Dict[str, Any]
    description: str = ""


class IncrementalStandardScaler:
    """
    增量标准化器
    使用 Welford 在线算法计算均值和方差
    """

    def __init__(self):
        self.n_samples = 0
        self.mean = None
        self.var = None
        self._initialized = False

    def partial_fit(self, X: np.ndarray) -> 'IncrementalStandardScaler':
        """
        增量更新统计量

        Args:
            X: 形状为 (n_samples, n_features) 的数组

        Returns:
            self
        """
        X = np.asarray(X, dtype=np.float64)

        if X.ndim == 1:
            X = X.reshape(-1, 1)

        for x in X:
            self.n_samples += 1

            if not self._initialized:
                self.mean = x.copy()
                self.var = np.zeros_like(x)
                self._initialized = True
            else:
                old_mean = self.mean.copy()
                self.mean += (x - self.mean) / self.n_samples
                self.var += (x - old_mean) * (x - self.mean)

        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """
        标准化数据

        Args:
            X: 输入数据

        Returns:
            标准化后的数据
        """
        if not self._initialized:
            raise RuntimeError("Scaler not fitted yet. Call partial_fit first.")

        X = np.asarray(X, dtype=np.float64)

        if X.ndim == 1:
            X = X.reshape(-1, 1)

        std = np.sqrt(self.var / max(self.n_samples - 1, 1))
        std[std == 0] = 1  # 避免除零

        return (X - self.mean) / std

    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        """增量更新并转换"""
        return self.partial_fit(X).transform(X)

    def get_state(self) -> Dict:
        """获取状态"""
        return {
            'n_samples': self.n_samples,
            'mean': self.mean.tolist() if self.mean is not None else None,
            'var': self.var.tolist() if self.var is not None else None,
            'initialized': self._initialized
        }

    def set_state(self, state: Dict):
        """恢复状态"""
        self.n_samples = state['n_samples']
        self.mean = np.array(state['mean']) if state['mean'] else None
        self.var = np.array(state['var']) if state['var'] else None
        self._initialized = state['initialized']


class OnlineLearner:
    """
    在线学习器
    支持增量训练和版本管理
    """

    def __init__(self, model_type: str = 'sgd', learning_rate: float = 0.01):
        """
        初始化在线学习器

        Args:
            model_type: 模型类型 ('sgd', 'passive_aggressive')
            learning_rate: 学习率
        """
        self.model_type = model_type
        self.learning_rate = learning_rate
        self.model = self._create_model()
        self.scaler = IncrementalStandardScaler()
        self.version = 0
        self.history: List[ModelVersion] = []
        self._total_samples = 0

    def _create_model(self):
        """创建增量学习模型"""
        try:
            from sklearn.linear_model import SGDRegressor

            return SGDRegressor(
                loss='squared_error',
                learning_rate='adaptive',
                eta0=self.learning_rate,
                random_state=42
            )
        except ImportError:
            raise ImportError("scikit-learn is required for online learning")

    def partial_fit(self, X: np.ndarray, y: np.ndarray,
                    description: str = "") -> Dict[str, Any]:
        """
        增量训练

        Args:
            X: 特征矩阵
            y: 目标值
            description: 更新描述

        Returns:
            训练指标
        """
        X = np.asarray(X, dtype=np.float64)
        y = np.asarray(y, dtype=np.float64)

        if X.ndim == 1:
            X = X.reshape(1, -1)

        # 增量标准化
        X_scaled = self.scaler.fit_transform(X)

        # 增量训练
        self.model.partial_fit(X_scaled, y)

        # 更新版本
        self.version += 1
        self._total_samples += len(X)

        # 计算指标
        y_pred = self.model.predict(X_scaled)
        mse = np.mean((y - y_pred) ** 2)
        r2 = 1 - mse / (np.var(y) + 1e-10)

        metrics = {
            'mse': float(mse),
            'r2': float(r2),
            'n_samples': len(X),
            'total_samples': self._total_samples
        }

        # 记录版本
        version_info = ModelVersion(
            version=self.version,
            timestamp=datetime.now().isoformat(),
            n_samples=self._total_samples,
            metrics=metrics,
            description=description
        )
        self.history.append(version_info)

        return metrics

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        预测

        Args:
            X: 特征矩阵

        Returns:
            预测值
        """
        if not self.scaler._initialized:
            raise RuntimeError("Model not trained yet. Call partial_fit first.")

        X = np.asarray(X, dtype=np.float64)

        if X.ndim == 1:
            X = X.reshape(1, -1)

        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)

    def get_metrics(self) -> Dict[str, Any]:
        """获取模型指标"""
        return {
            'version': self.version,
            'total_samples': self._total_samples,
            'model_type': self.model_type,
            'learning_rate': self.learning_rate,
            'history': [asdict(v) for v in self.history[-10:]]
        }

    def save(self, path: str):
        """
        保存模型

        Args:
            path: 保存路径
        """
        state = {
            'model': self.model,
            'scaler': self.scaler.get_state(),
            'version': self.version,
            'history': [asdict(v) for v in self.history],
            'total_samples': self._total_samples,
            'model_type': self.model_type,
            'learning_rate': self.learning_rate
        }

        os.makedirs(os.path.dirname(path), exist_ok=True)

        with open(path, 'wb') as f:
            pickle.dump(state, f)

    def load(self, path: str):
        """
        加载模型

        Args:
            path: 模型路径
        """
        with open(path, 'rb') as f:
            state = pickle.load(f)

        self.model = state['model']
        self.scaler.set_state(state['scaler'])
        self.version = state['version']
        self.history = [ModelVersion(**v) for v in state['history']]
        self._total_samples = state['total_samples']
        self.model_type = state['model_type']
        self.learning_rate = state['learning_rate']

    def get_feature_importance(self) -> Optional[np.ndarray]:
        """获取特征重要性 (仅适用于线性模型)"""
        if hasattr(self.model, 'coef_'):
            return self.model.coef_
        return None


class ModelManager:
    """
    模型版本管理器
    支持多版本保存、加载和回滚
    """

    def __init__(self, model_dir: str = 'models'):
        """
        初始化模型管理器

        Args:
            model_dir: 模型保存目录
        """
        self.model_dir = model_dir
        self.versions_file = os.path.join(model_dir, 'versions.json')
        self.versions: Dict[int, ModelVersion] = {}
        self._next_version = 1  # 管理器自己的版本计数器

        os.makedirs(model_dir, exist_ok=True)
        self._load_versions()

    def _load_versions(self):
        """加载版本信息"""
        if os.path.exists(self.versions_file):
            with open(self.versions_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.versions = {
                    int(k): ModelVersion(**v) for k, v in data.items()
                }
            # 恢复版本计数器
            if self.versions:
                self._next_version = max(self.versions.keys()) + 1

    def _save_versions(self):
        """保存版本信息"""
        data = {
            str(k): asdict(v) for k, v in self.versions.items()
        }
        with open(self.versions_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def save_model(self, model: OnlineLearner, description: str = "") -> int:
        """
        保存模型版本

        Args:
            model: 在线学习器
            description: 版本描述

        Returns:
            版本号
        """
        version = self._next_version
        model_path = os.path.join(self.model_dir, f'model_v{version}.pkl')

        # 保存模型
        model.save(model_path)

        # 记录版本信息
        version_info = ModelVersion(
            version=version,
            timestamp=datetime.now().isoformat(),
            n_samples=model._total_samples,
            metrics=model.get_metrics(),
            description=description
        )
        self.versions[version] = version_info
        self._next_version += 1
        self._save_versions()

        return version

    def load_model(self, version: Optional[int] = None) -> OnlineLearner:
        """
        加载模型

        Args:
            version: 版本号 (默认加载最新版本)

        Returns:
            在线学习器
        """
        if not self.versions:
            raise ValueError("No saved models found")

        if version is None:
            version = max(self.versions.keys())

        if version not in self.versions:
            raise ValueError(f"Version {version} not found")

        model_path = os.path.join(self.model_dir, f'model_v{version}.pkl')

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")

        model = OnlineLearner()
        model.load(model_path)

        return model

    def list_versions(self) -> List[Dict[str, Any]]:
        """
        列出所有版本

        Returns:
            版本信息列表
        """
        return [
            {
                'version': v.version,
                'timestamp': v.timestamp,
                'n_samples': v.n_samples,
                'description': v.description
            }
            for v in sorted(self.versions.values(), key=lambda x: x.version)
        ]

    def get_latest_version(self) -> int:
        """获取最新版本号"""
        if not self.versions:
            return 0
        return max(self.versions.keys())

    def rollback(self, version: int) -> OnlineLearner:
        """
        回滚到指定版本

        Args:
            version: 目标版本号

        Returns:
            加载的模型
        """
        return self.load_model(version)

    def delete_version(self, version: int):
        """
        删除指定版本

        Args:
            version: 版本号
        """
        if version in self.versions:
            model_path = os.path.join(self.model_dir, f'model_v{version}.pkl')
            if os.path.exists(model_path):
                os.remove(model_path)
            del self.versions[version]
            self._save_versions()

    def cleanup(self, keep_last: int = 5):
        """
        清理旧版本

        Args:
            keep_last: 保留最近的版本数
        """
        if len(self.versions) <= keep_last:
            return

        sorted_versions = sorted(self.versions.keys())
        versions_to_delete = sorted_versions[:-keep_last]

        for version in versions_to_delete:
            self.delete_version(version)


# 便捷函数
def create_online_learner(model_type: str = 'sgd',
                          learning_rate: float = 0.01) -> OnlineLearner:
    """创建在线学习器"""
    return OnlineLearner(model_type, learning_rate)


def create_model_manager(model_dir: str = 'models') -> ModelManager:
    """创建模型管理器"""
    return ModelManager(model_dir)
