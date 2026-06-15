"""
在线学习器测试
"""

import pytest
import numpy as np
import pandas as pd
import tempfile
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from skills.stock_recommender.online_learner import (
    OnlineLearner,
    IncrementalStandardScaler,
    ModelManager,
    ModelVersion,
    create_online_learner,
    create_model_manager
)


class TestIncrementalStandardScaler:
    """增量标准化器测试"""

    def test_init(self):
        """测试初始化"""
        scaler = IncrementalStandardScaler()
        assert scaler.n_samples == 0
        assert scaler.mean is None
        assert scaler.var is None
        assert not scaler._initialized

    def test_partial_fit(self):
        """测试增量拟合"""
        scaler = IncrementalStandardScaler()
        X = np.array([[1, 2], [3, 4], [5, 6]])

        scaler.partial_fit(X)

        assert scaler.n_samples == 3
        assert scaler._initialized
        assert np.allclose(scaler.mean, [3, 4])

    def test_multiple_partial_fit(self):
        """测试多次增量拟合"""
        scaler = IncrementalStandardScaler()

        scaler.partial_fit(np.array([[1, 2]]))
        assert scaler.n_samples == 1

        scaler.partial_fit(np.array([[3, 4]]))
        assert scaler.n_samples == 2

        scaler.partial_fit(np.array([[5, 6]]))
        assert scaler.n_samples == 3

    def test_transform(self):
        """测试转换"""
        scaler = IncrementalStandardScaler()
        X = np.array([[1, 2], [3, 4], [5, 6]])

        scaler.partial_fit(X)
        X_scaled = scaler.transform(X)

        assert X_scaled.shape == X.shape
        # 标准化后均值应接近 0
        assert np.allclose(X_scaled.mean(axis=0), [0, 0], atol=1e-10)

    def test_fit_transform(self):
        """测试拟合并转换"""
        scaler = IncrementalStandardScaler()
        X = np.array([[1, 2], [3, 4], [5, 6]])

        X_scaled = scaler.fit_transform(X)

        assert X_scaled.shape == X.shape
        assert scaler.n_samples == 3

    def test_transform_before_fit(self):
        """测试拟合前转换"""
        scaler = IncrementalStandardScaler()

        with pytest.raises(RuntimeError, match="not fitted"):
            scaler.transform(np.array([[1, 2]]))

    def test_get_set_state(self):
        """测试状态保存恢复"""
        scaler = IncrementalStandardScaler()
        X = np.array([[1, 2], [3, 4]])
        scaler.partial_fit(X)

        state = scaler.get_state()
        assert state['n_samples'] == 2
        assert state['initialized']

        new_scaler = IncrementalStandardScaler()
        new_scaler.set_state(state)
        assert new_scaler.n_samples == 2

    def test_single_dimension(self):
        """测试单维数据"""
        scaler = IncrementalStandardScaler()
        X = np.array([1, 2, 3, 4, 5])

        X_scaled = scaler.fit_transform(X)

        assert X_scaled.shape == (5, 1)


class TestOnlineLearner:
    """在线学习器测试"""

    def test_init(self):
        """测试初始化"""
        learner = OnlineLearner()
        assert learner.model_type == 'sgd'
        assert learner.version == 0
        assert learner._total_samples == 0

    def test_partial_fit(self):
        """测试增量训练"""
        learner = OnlineLearner()

        X = np.random.randn(10, 5)
        y = np.random.randn(10)

        metrics = learner.partial_fit(X, y)

        assert 'mse' in metrics
        assert 'r2' in metrics
        assert metrics['n_samples'] == 10
        assert learner.version == 1
        assert learner._total_samples == 10

    def test_multiple_partial_fit(self):
        """测试多次增量训练"""
        learner = OnlineLearner()

        for i in range(5):
            X = np.random.randn(10, 5)
            y = np.random.randn(10)
            learner.partial_fit(X, y)

        assert learner.version == 5
        assert learner._total_samples == 50

    def test_predict(self):
        """测试预测"""
        learner = OnlineLearner()

        # 训练
        X_train = np.random.randn(50, 5)
        y_train = np.random.randn(50)
        learner.partial_fit(X_train, y_train)

        # 预测
        X_test = np.random.randn(10, 5)
        predictions = learner.predict(X_test)

        assert len(predictions) == 10

    def test_predict_before_train(self):
        """测试训练前预测"""
        learner = OnlineLearner()

        with pytest.raises(RuntimeError, match="not trained"):
            learner.predict(np.array([[1, 2, 3]]))

    def test_get_metrics(self):
        """测试获取指标"""
        learner = OnlineLearner()

        X = np.random.randn(10, 5)
        y = np.random.randn(10)
        learner.partial_fit(X, y, description="test")

        metrics = learner.get_metrics()

        assert metrics['version'] == 1
        assert metrics['total_samples'] == 10
        assert metrics['model_type'] == 'sgd'
        assert len(metrics['history']) == 1

    def test_save_load(self):
        """测试保存加载"""
        learner = OnlineLearner()

        X = np.random.randn(20, 5)
        y = np.random.randn(20)
        learner.partial_fit(X, y)

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, 'model.pkl')
            learner.save(path)

            new_learner = OnlineLearner()
            new_learner.load(path)

            assert new_learner.version == 1
            assert new_learner._total_samples == 20

            # 预测应相同
            X_test = np.random.randn(5, 5)
            pred1 = learner.predict(X_test)
            pred2 = new_learner.predict(X_test)
            assert np.allclose(pred1, pred2)

    def test_feature_importance(self):
        """测试特征重要性"""
        learner = OnlineLearner()

        X = np.random.randn(50, 5)
        y = np.random.randn(50)
        learner.partial_fit(X, y)

        importance = learner.get_feature_importance()

        assert importance is not None
        assert len(importance) == 5

    def test_create_online_learner(self):
        """测试创建在线学习器"""
        learner = create_online_learner('sgd', 0.01)
        assert isinstance(learner, OnlineLearner)


class TestModelManager:
    """模型管理器测试"""

    def test_init(self):
        """测试初始化"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ModelManager(tmpdir)
            assert len(manager.versions) == 0

    def test_save_model(self):
        """测试保存模型"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ModelManager(tmpdir)
            learner = OnlineLearner()

            X = np.random.randn(20, 5)
            y = np.random.randn(20)
            learner.partial_fit(X, y)

            version = manager.save_model(learner, "test version")

            assert version == 1
            assert 1 in manager.versions

    def test_load_model(self):
        """测试加载模型"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ModelManager(tmpdir)
            learner = OnlineLearner()

            X = np.random.randn(20, 5)
            y = np.random.randn(20)
            learner.partial_fit(X, y)

            manager.save_model(learner, "v1")

            loaded = manager.load_model(1)
            assert loaded.version == 1

    def test_load_latest(self):
        """测试加载最新版本"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ModelManager(tmpdir)

            for i in range(3):
                learner = OnlineLearner()
                X = np.random.randn(10, 5)
                y = np.random.randn(10)
                learner.partial_fit(X, y)
                manager.save_model(learner, f"v{i+1}")

            latest = manager.load_model()
            # 模型内部 version 是 partial_fit 次数 (1)
            # ModelManager 的版本号是 3
            assert latest.version == 1
            assert manager.get_latest_version() == 3

    def test_list_versions(self):
        """测试列出版本"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ModelManager(tmpdir)

            for i in range(3):
                learner = OnlineLearner()
                X = np.random.randn(10, 5)
                y = np.random.randn(10)
                learner.partial_fit(X, y)
                manager.save_model(learner, f"v{i+1}")

            versions = manager.list_versions()
            assert len(versions) == 3

    def test_rollback(self):
        """测试回滚"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ModelManager(tmpdir)

            # 创建两个版本
            learner1 = OnlineLearner()
            X = np.random.randn(10, 5)
            y = np.random.randn(10)
            learner1.partial_fit(X, y)
            manager.save_model(learner1, "v1")

            learner2 = OnlineLearner()
            X = np.random.randn(20, 5)
            y = np.random.randn(20)
            learner2.partial_fit(X, y)
            manager.save_model(learner2, "v2")

            # 回滚到 v1
            rolled_back = manager.rollback(1)
            assert rolled_back.version == 1

    def test_cleanup(self):
        """测试清理"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ModelManager(tmpdir)

            for i in range(10):
                learner = OnlineLearner()
                X = np.random.randn(10, 5)
                y = np.random.randn(10)
                learner.partial_fit(X, y)
                manager.save_model(learner, f"v{i+1}")

            assert len(manager.versions) == 10

            manager.cleanup(keep_last=3)

            assert len(manager.versions) == 3

    def test_load_not_found(self):
        """测试加载不存在的版本"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ModelManager(tmpdir)

            with pytest.raises(ValueError, match="No saved models"):
                manager.load_model()

    def test_create_model_manager(self):
        """测试创建模型管理器"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = create_model_manager(tmpdir)
            assert isinstance(manager, ModelManager)


class TestIntegration:
    """集成测试"""

    def test_online_update_flow(self):
        """测试完整在线更新流程"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建管理器
            manager = ModelManager(tmpdir)

            # 创建学习器并训练
            learner = OnlineLearner(learning_rate=0.01)

            # 第一批数据
            X1 = np.random.randn(50, 5)
            y1 = X1.sum(axis=1) + np.random.randn(50) * 0.1
            metrics1 = learner.partial_fit(X1, y1, "initial training")
            assert metrics1['r2'] > 0.5  # 应该有较好的拟合

            # 保存版本 1
            manager.save_model(learner, "initial model")

            # 第二批数据
            X2 = np.random.randn(30, 5)
            y2 = X2.sum(axis=1) + np.random.randn(30) * 0.1
            metrics2 = learner.partial_fit(X2, y2, "incremental update")

            # 保存版本 2
            manager.save_model(learner, "after update")

            # 验证版本
            versions = manager.list_versions()
            assert len(versions) == 2

            # 加载最新版本预测
            latest = manager.load_model()
            X_test = np.random.randn(5, 5)
            predictions = latest.predict(X_test)
            assert len(predictions) == 5

    def test_multiple_stock_update(self):
        """测试多股票增量更新"""
        learner = OnlineLearner()

        # 模拟多只股票的数据更新
        for stock_id in range(5):
            X = np.random.randn(20, 8)
            y = np.random.randn(20)
            metrics = learner.partial_fit(X, y, f"stock_{stock_id}")

        assert learner.version == 5
        assert learner._total_samples == 100

        # 预测
        X_test = np.random.randn(3, 8)
        predictions = learner.predict(X_test)
        assert len(predictions) == 3


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
