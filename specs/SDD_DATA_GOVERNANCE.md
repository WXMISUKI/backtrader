# 软件设计规格说明 (SDD)
# Data Governance: 数据治理与缓存层

---

## 文档信息

| 项目 | 内容 |
|------|------|
| 文档名称 | 数据治理与缓存层 SDD |
| 版本 | v0.1 |
| 创建日期 | 2026-06-17 |
| 状态 | 草案 |

---

## 1. 背景

项目当前已经能通过东方财富、akshare 和 mock 路径获取数据，但真实数据链路存在不稳定、接口偶发失败、数据返回不一致等问题。

为了让上层的 `StockOrchestrator`、智能体和推荐系统更稳定，需要引入一层统一的数据治理能力。

---

## 2. 目标

### 2.1 总目标

建立一个最小可用的数据治理层，对行情、基本面和市场数据进行缓存、校验、降级和来源追踪。

### 2.2 具体目标

| 目标 | 说明 |
|------|------|
| 缓存统一 | 统一管理短期缓存 |
| 质量统一 | 统一检查数据完整性和合法性 |
| 降级统一 | 真实数据失败时可控回退 |
| 来源统一 | 明确标记 real / mock / cache / config |
| 上游友好 | 为编排器提供稳定的数据视图 |

---

## 3. 范围

### 3.1 纳入范围

- 行情数据缓存
- 财务数据缓存
- 市场概览缓存
- 数据质量校验
- 降级标记和来源记录

### 3.2 不纳入范围

- 持久化数据库
- 分布式缓存
- 实时推送系统
- 数据仓库建设

---

## 4. 核心设计

### 4.1 CacheManager

负责统一的内存缓存管理。

#### 当前实现状态

- 已实现 `core/data/governance.py`
- 已支持 `get / set / clear`
- 已支持 TTL 过期管理

核心能力：

- 按 key 读写缓存
- TTL 过期管理
- 支持覆盖写入
- 支持缓存命中统计

### 4.2 DataQualityChecker

负责对数据进行轻量质量检查。

#### 当前实现状态

- 已实现 `check_dataframe`
- 已实现 `check_dict`
- 已支持空数据和非法类型识别

核心能力：

- 检查是否为空
- 检查字段完整性
- 检查时间字段合法性
- 检查数值是否异常

### 4.3 DataSnapshot

负责描述一次数据获取结果。

#### 当前实现状态

- 已实现 `DataSnapshot`
- 已实现 `build_snapshot`
- 已支持来源、降级和缓存命中标记

建议字段：

- `name`
- `source`
- `fetched_at`
- `is_degraded`
- `cache_hit`
- `payload`
- `reason`

---

## 5. 核心接口

```python
class CacheManager:
    def get(self, key: str) -> Any: ...
    def set(self, key: str, value: Any, ttl: int = 3600) -> None: ...
    def clear(self) -> None: ...

class DataQualityChecker:
    def check_dataframe(self, df) -> dict: ...
    def check_dict(self, data: dict) -> dict: ...

class DataSnapshot:
    def to_dict(self) -> dict: ...
```

---

## 6. 数据来源约定

| 来源 | 含义 |
|------|------|
| real | 来自真实外部数据源 |
| mock | 来自降级或模拟数据 |
| cache | 来自缓存 |
| config | 来自配置 |
| unknown | 无法识别来源 |

---

## 7. 验收标准

- 能缓存至少两类数据
- 能标记是否命中缓存
- 能识别数据是否降级
- 能给上游返回统一的来源描述

---

## 8. 下一步建议

1. 先封装行情和财务两条数据路径
2. 再把市场概览纳入治理
3. 最后接入 `StockOrchestrator`

---

## 9. 实现归档

### 已完成

- `core/data/governance.py`
- `core/data/__init__.py`

### 验证结果

- 缓存读写正常
- 质量检查正常
- 快照生成正常
