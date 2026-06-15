# SDD: 在线模型更新模块

## 1. 概述

### 1.1 目标
为 MLRecommender 添加在线学习能力，支持模型增量更新、版本管理和自动定时更新。

### 1.2 背景
当前 MLRecommender 的问题：
- 模型训练是一次性的，无法适应市场变化
- 没有模型版本管理，无法回滚
- 没有自动更新机制

### 1.3 设计来源
- River (Python在线学习库)
- scikit-learn 的 `partial_fit()` 方法
- MLOps 最佳实践

## 2. 架构设计

### 2.1 模块结构

```
skills/stock_recommender/
├── ml_recommender.py      # 现有 ML 推荐器
├── online_learner.py      # 新增: 在线学习器
├── model_manager.py       # 新增: 模型版本管理
└── __init__.py            # 更新导出
```

### 2.2 核心类

#### OnlineLearner (在线学习器)

```python
class OnlineLearner:
    """支持增量学习的在线模型"""

    def __init__(self, base_model='sgd', learning_rate=0.01):
        self.model = self._create_model(base_model)
        self.scaler = IncrementalStandardScaler()
        self.version = 0
        self.history = []

    def partial_fit(self, X, y):
        """增量训练"""
        X_scaled = self.scaler.partial_fit_transform(X)
        self.model.partial_fit(X_scaled, y)
        self.version += 1

    def predict(self, X):
        """预测"""
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)

    def get_metrics(self):
        """获取模型指标"""
        return {
            'version': self.version,
            'n_samples': self.scaler.n_samples,
            'history': self.history[-10:]  # 最近10次更新
        }
```

#### ModelManager (模型管理器)

```python
class ModelManager:
    """模型版本管理"""

    def __init__(self, model_dir='models/'):
        self.model_dir = model_dir
        self.versions = {}

    def save_model(self, model, version, metadata=None):
        """保存模型版本"""
        path = f"{self.model_dir}/model_v{version}.pkl"
        # 保存模型 + 元数据

    def load_model(self, version=None):
        """加载模型版本 (默认最新)"""
        if version is None:
            version = self.get_latest_version()
        # 加载并返回

    def list_versions(self):
        """列出所有版本"""
        return self.versions

    def rollback(self, version):
        """回滚到指定版本"""
        return self.load_model(version)
```

#### IncrementalStandardScaler (增量标准化器)

```python
class IncrementalStandardScaler:
    """支持增量更新的标准化器"""

    def __init__(self):
        self.n_samples = 0
        self.mean = None
        self.var = None

    def partial_fit_transform(self, X):
        """增量更新并转换"""
        # Welford's online algorithm
        for x in X:
            self.n_samples += 1
            old_mean = self.mean
            self.mean += (x - self.mean) / self.n_samples
            self.var += (x - old_mean) * (x - self.mean)
        return self.transform(X)

    def transform(self, X):
        """标准化"""
        return (X - self.mean) / np.sqrt(self.var / self.n_samples)
```

## 3. 功能设计

### 3.1 增量学习

| 功能 | 描述 |
|------|------|
| partial_fit() | 支持小批量数据增量训练 |
| 增量标准化 | 使用 Welford 算法在线更新均值/方差 |
| 学习率衰减 | 随训练次数衰减学习率 |

### 3.2 模型版本管理

| 功能 | 描述 |
|------|------|
| 自动版本号 | 每次更新自动递增版本号 |
| 元数据记录 | 记录训练样本数、指标、时间等 |
| 模型回滚 | 支持回滚到历史版本 |
| 版本对比 | 对比不同版本的性能 |

### 3.3 定时更新

| 功能 | 描述 |
|------|------|
| 定时任务 | 支持每日/每周自动更新 |
| 增量数据 | 只获取新数据进行训练 |
| 更新通知 | 更新完成后发送通知 |

## 4. 接口设计

### 4.1 OnlineLearner 接口

```python
# 创建在线学习器
learner = OnlineLearner(base_model='sgd', learning_rate=0.01)

# 增量训练
learner.partial_fit(X_new, y_new)

# 预测
predictions = learner.predict(X_test)

# 获取状态
metrics = learner.get_metrics()

# 保存/加载
learner.save('models/online_model.pkl')
learner.load('models/online_model.pkl')
```

### 4.2 ModelManager 接口

```python
# 创建管理器
manager = ModelManager(model_dir='models/')

# 保存模型
manager.save_model(model, version=1, metadata={'accuracy': 0.85})

# 加载模型
model = manager.load_model()  # 最新版本
model = manager.load_model(version=3)  # 指定版本

# 列出版本
versions = manager.list_versions()

# 回滚
model = manager.rollback(version=2)
```

## 5. 数据流

```
新数据到达
    │
    ▼
┌─────────────────┐
│  数据预处理     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  增量标准化     │  ← IncrementalStandardScaler
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  增量训练       │  ← partial_fit()
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  评估指标       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  保存版本       │  ← ModelManager
└─────────────────┘
```

## 6. 测试计划

### 6.1 单元测试

| 测试项 | 描述 |
|--------|------|
| test_partial_fit | 测试增量训练功能 |
| test_incremental_scaler | 测试增量标准化 |
| test_model_save_load | 测试模型保存加载 |
| test_version_management | 测试版本管理 |
| test_rollback | 测试模型回滚 |

### 6.2 集成测试

| 测试项 | 描述 |
|--------|------|
| test_online_update_flow | 测试完整在线更新流程 |
| test_multiple_updates | 测试多次增量更新 |

## 7. 依赖

- scikit-learn (已有)
- pickle (标准库)
- threading (标准库, 用于定时任务)
- datetime (标准库)

## 8. 风险与缓解

| 风险 | 缓解措施 |
|------|---------|
| 模型漂移 | 定期全量重训练 |
| 数据质量 | 添加数据验证 |
| 存储空间 | 自动清理旧版本 |
