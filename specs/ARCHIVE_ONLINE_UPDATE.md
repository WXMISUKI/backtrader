# 归档: 在线模型更新模块

## 1. 完成日期
2026-06-14

## 2. 功能清单

| 功能 | 状态 | 测试覆盖 |
|------|------|---------|
| IncrementalStandardScaler | ✅ | 8 tests |
| OnlineLearner | ✅ | 9 tests |
| ModelManager | ✅ | 9 tests |
| 集成测试 | ✅ | 2 tests |

## 3. 文件清单

### 3.1 实现文件

| 文件 | 描述 |
|------|------|
| `skills/stock_recommender/online_learner.py` | 在线学习器模块 |

### 3.2 测试文件

| 文件 | 测试数 | 状态 |
|------|--------|------|
| `tests/test_online_learner.py` | 28 | ✅ 全部通过 |

### 3.3 规格文件

| 文件 | 描述 |
|------|------|
| `specs/SDD_ONLINE_UPDATE.md` | 规格说明 |

## 4. 核心类

### 4.1 IncrementalStandardScaler

增量标准化器，使用 Welford 在线算法。

```python
scaler = IncrementalStandardScaler()
scaler.partial_fit(X1)
scaler.partial_fit(X2)
X_scaled = scaler.transform(X_new)
```

**方法:**
- `partial_fit(X)`: 增量更新均值和方差
- `transform(X)`: 标准化数据
- `fit_transform(X)`: 增量更新并转换
- `get_state()`: 获取状态
- `set_state(state)`: 恢复状态

### 4.2 OnlineLearner

在线学习器，支持增量训练。

```python
learner = OnlineLearner(model_type='sgd', learning_rate=0.01)
metrics = learner.partial_fit(X, y, description="update")
predictions = learner.predict(X_new)
learner.save('model.pkl')
```

**方法:**
- `partial_fit(X, y, description)`: 增量训练
- `predict(X)`: 预测
- `get_metrics()`: 获取指标
- `save(path)`: 保存模型
- `load(path)`: 加载模型
- `get_feature_importance()`: 获取特征重要性

### 4.3 ModelManager

模型版本管理器。

```python
manager = ModelManager(model_dir='models/')
version = manager.save_model(learner, "description")
model = manager.load_model()  # 最新版本
model = manager.load_model(version=2)  # 指定版本
versions = manager.list_versions()
model = manager.rollback(version=1)
manager.cleanup(keep_last=5)
```

**方法:**
- `save_model(model, description)`: 保存模型版本
- `load_model(version)`: 加载模型
- `list_versions()`: 列出所有版本
- `get_latest_version()`: 获取最新版本号
- `rollback(version)`: 回滚到指定版本
- `delete_version(version)`: 删除版本
- `cleanup(keep_last)`: 清理旧版本

## 5. 测试结果

```
============================= 28 passed in 2.56s ==============================

tests/test_online_learner.py::TestIncrementalStandardScaler::test_init PASSED
tests/test_online_learner.py::TestIncrementalStandardScaler::test_partial_fit PASSED
tests/test_online_learner.py::TestIncrementalStandardScaler::test_multiple_partial_fit PASSED
tests/test_online_learner.py::TestIncrementalStandardScaler::test_transform PASSED
tests/test_online_learner.py::TestIncrementalStandardScaler::test_fit_transform PASSED
tests/test_online_learner.py::TestIncrementalStandardScaler::test_transform_before_fit PASSED
tests/test_online_learner.py::TestIncrementalStandardScaler::test_get_set_state PASSED
tests/test_online_learner.py::TestIncrementalStandardScaler::test_single_dimension PASSED
tests/test_online_learner.py::TestOnlineLearner::test_init PASSED
tests/test_online_learner.py::TestOnlineLearner::test_partial_fit PASSED
tests/test_online_learner.py::TestOnlineLearner::test_multiple_partial_fit PASSED
tests/test_online_learner.py::TestOnlineLearner::test_predict PASSED
tests/test_online_learner.py::TestOnlineLearner::test_predict_before_train PASSED
tests/test_online_learner.py::TestOnlineLearner::test_get_metrics PASSED
tests/test_online_learner.py::TestOnlineLearner::test_save_load PASSED
tests/test_online_learner.py::TestOnlineLearner::test_feature_importance PASSED
tests/test_online_learner.py::TestOnlineLearner::test_create_online_learner PASSED
tests/test_online_learner.py::TestModelManager::test_init PASSED
tests/test_online_learner.py::TestModelManager::test_save_model PASSED
tests/test_online_learner.py::TestModelManager::test_load_model PASSED
tests/test_online_learner.py::TestModelManager::test_load_latest PASSED
tests/test_online_learner.py::TestModelManager::test_list_versions PASSED
tests/test_online_learner.py::TestModelManager::test_rollback PASSED
tests/test_online_learner.py::TestModelManager::test_cleanup PASSED
tests/test_online_learner.py::TestModelManager::test_load_not_found PASSED
tests/test_online_learner.py::TestModelManager::test_create_model_manager PASSED
tests/test_online_learner.py::TestIntegration::test_online_update_flow PASSED
tests/test_online_learner.py::TestIntegration::test_multiple_stock_update PASSED
```

## 6. 使用示例

### 6.1 基本使用

```python
from skills.stock_recommender import OnlineLearner, ModelManager

# 创建学习器
learner = OnlineLearner(learning_rate=0.01)

# 增量训练
X_batch1 = get_batch1()
y_batch1 = get_labels1()
metrics = learner.partial_fit(X_batch1, y_batch1, "batch 1")
print(f"MSE: {metrics['mse']:.4f}, R²: {metrics['r2']:.4f}")

# 继续训练
X_batch2 = get_batch2()
y_batch2 = get_labels2()
learner.partial_fit(X_batch2, y_batch2, "batch 2")

# 预测
predictions = learner.predict(X_new)
```

### 6.2 版本管理

```python
from skills.stock_recommender import ModelManager

manager = ModelManager('models/')

# 保存版本
v1 = manager.save_model(learner, "initial model")

# 继续训练后保存新版本
learner.partial_fit(X_new, y_new)
v2 = manager.save_model(learner, "updated model")

# 列出版本
versions = manager.list_versions()
for v in versions:
    print(f"v{v['version']}: {v['description']}")

# 回滚到旧版本
old_model = manager.rollback(v1)

# 清理旧版本
manager.cleanup(keep_last=3)
```

### 6.3 定时更新

```python
import schedule
import time

def update_model():
    """定时更新模型"""
    new_data = fetch_new_data()
    X, y = prepare_data(new_data)
    learner.partial_fit(X, y, f"auto update {datetime.now()}")
    manager.save_model(learner, "auto update")

# 每天更新
schedule.every().day.at("18:00").do(update_model)

while True:
    schedule.run_pending()
    time.sleep(60)
```

## 7. 技术要点

### 7.1 Welford 在线算法

用于增量计算均值和方差，避免存储所有历史数据：

```python
# 对于新样本 x:
mean_new = mean_old + (x - mean_old) / n
var_new = var_old + (x - mean_old) * (x - mean_new)
```

### 7.2 SGD 增量学习

使用 scikit-learn 的 SGDRegressor，支持 `partial_fit()` 方法：

```python
from sklearn.linear_model import SGDRegressor
model = SGDRegressor(loss='squared_error', learning_rate='adaptive')
model.partial_fit(X, y)
```

### 7.3 版本管理

ModelManager 使用 JSON 文件记录版本信息，pickle 保存模型：

```
models/
├── versions.json      # 版本元数据
├── model_v1.pkl       # 模型文件
├── model_v2.pkl
└── model_v3.pkl
```

## 8. 已知限制

1. **模型类型**: 目前仅支持线性模型 (SGD)，可扩展支持其他增量学习算法
2. **标签质量**: 当前使用模拟标签，实际应用需要真实收益数据
3. **特征工程**: 特征固定，可扩展自动特征选择
4. **更新频率**: 需要手动或定时触发，可扩展实时更新

## 9. 后续优化

1. 支持更多增量学习算法 (Passive Aggressive, 在线随机森林)
2. 添加模型性能监控和漂移检测
3. 支持分布式增量训练
4. 添加 A/B 测试框架
