#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
模型治理与发布门禁

提供轻量的模型版本、特征清单、评估门禁和回滚支持。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import threading
from typing import Any, Dict, Iterable, List, Optional
import uuid


_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_STORE_PATH = _PROJECT_ROOT / "models" / "model_governance.json"


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_features(features: Iterable[str]) -> List[str]:
    normalized: List[str] = []
    for feature in features:
        value = str(feature).strip()
        if value:
            normalized.append(value)
    return normalized


def _compute_feature_hash(features: Iterable[str]) -> str:
    normalized = _normalize_features(features)
    joined = "|".join(normalized)
    return hashlib.sha1(joined.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class FeatureManifest:
    """特征清单。"""

    manifest_id: str
    name: str
    version: str
    features: List[str] = field(default_factory=list)
    feature_hash: str = ""
    description: str = ""
    source: str = ""
    created_at: str = field(default_factory=_utcnow)
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["features"] = list(self.features)
        payload["meta"] = dict(self.meta)
        return payload


@dataclass(frozen=True)
class ModelRecord:
    """模型治理记录。"""

    model_name: str
    version: str
    status: str = "draft"
    artifact_path: str = ""
    metrics: Dict[str, Any] = field(default_factory=dict)
    thresholds: Dict[str, Any] = field(default_factory=dict)
    feature_manifest: Dict[str, Any] = field(default_factory=dict)
    notes: str = ""
    created_at: str = field(default_factory=_utcnow)
    updated_at: str = field(default_factory=_utcnow)
    last_decision: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["metrics"] = dict(self.metrics)
        payload["thresholds"] = dict(self.thresholds)
        payload["feature_manifest"] = dict(self.feature_manifest)
        payload["last_decision"] = dict(self.last_decision)
        return payload


@dataclass(frozen=True)
class ReleaseDecision:
    """模型发布决策。"""

    model_name: str
    version: str
    decision: str
    ok: bool
    score: float
    reasons: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    thresholds: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_utcnow)

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["reasons"] = list(self.reasons)
        payload["metrics"] = dict(self.metrics)
        payload["thresholds"] = dict(self.thresholds)
        return payload


def build_feature_manifest(
    name: str,
    features: Iterable[str],
    *,
    version: str = "v1",
    description: str = "",
    source: str = "",
    meta: Optional[Dict[str, Any]] = None,
) -> FeatureManifest:
    """构建特征清单。"""
    normalized = _normalize_features(features)
    return FeatureManifest(
        manifest_id=str(uuid.uuid4()),
        name=name,
        version=version,
        features=normalized,
        feature_hash=_compute_feature_hash(normalized),
        description=description,
        source=source,
        meta=dict(meta or {}),
    )


class ModelGovernanceStore:
    """本地模型治理存储。"""

    def __init__(self, path: Optional[str] = None) -> None:
        self.path = Path(path) if path else _DEFAULT_STORE_PATH
        self._lock = threading.Lock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._state = self._load()

    def _load(self) -> dict:
        if not self.path.exists():
            return {
                "feature_manifests": {},
                "models": {},
                "stable_versions": {},
                "events": [],
            }
        try:
            with self.path.open("r", encoding="utf-8") as f:
                state = json.load(f)
        except Exception:
            state = {}

        state.setdefault("feature_manifests", {})
        state.setdefault("models", {})
        state.setdefault("stable_versions", {})
        state.setdefault("events", [])
        return state

    def _save(self) -> None:
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(self._state, f, ensure_ascii=False, indent=2, default=str)

    def upsert_manifest(self, manifest: FeatureManifest) -> dict:
        payload = manifest.to_dict()
        with self._lock:
            self._state.setdefault("feature_manifests", {})[manifest.manifest_id] = payload
            self._append_event(
                {
                    "event": "feature_manifest_registered",
                    "manifest_id": manifest.manifest_id,
                    "name": manifest.name,
                    "version": manifest.version,
                    "feature_hash": manifest.feature_hash,
                    "created_at": _utcnow(),
                }
            )
            self._save()
        return payload

    def upsert_model(self, record: ModelRecord) -> dict:
        payload = record.to_dict()
        with self._lock:
            models = self._state.setdefault("models", {})
            model_bucket = models.setdefault(record.model_name, {})
            model_bucket[record.version] = payload
            if record.status == "stable":
                self._state.setdefault("stable_versions", {})[record.model_name] = record.version
            self._append_event(
                {
                    "event": "model_registered",
                    "model_name": record.model_name,
                    "version": record.version,
                    "status": record.status,
                    "created_at": _utcnow(),
                }
            )
            self._save()
        return payload

    def update_model(self, model_name: str, version: str, **changes: Any) -> dict:
        with self._lock:
            record = self._state.get("models", {}).get(model_name, {}).get(version)
            if record is None:
                raise KeyError(f"model not found: {model_name}@{version}")
            record.update(changes)
            record["updated_at"] = _utcnow()
            if record.get("status") == "stable":
                self._state.setdefault("stable_versions", {})[model_name] = version
            self._append_event(
                {
                    "event": "model_updated",
                    "model_name": model_name,
                    "version": version,
                    "changes": list(changes.keys()),
                    "created_at": _utcnow(),
                }
            )
            self._save()
            return dict(record)

    def list_manifests(self) -> List[dict]:
        manifests = list(self._state.get("feature_manifests", {}).values())
        return sorted(manifests, key=lambda item: (item.get("name", ""), item.get("version", "")))

    def list_models(self, model_name: Optional[str] = None) -> List[dict]:
        models = self._state.get("models", {})
        records: List[dict] = []
        for name, versions in models.items():
            if model_name and name != model_name:
                continue
            records.extend(versions.values())
        return sorted(records, key=lambda item: (item.get("created_at", ""), item.get("model_name", ""), item.get("version", "")))

    def get_model(self, model_name: str, version: str) -> Optional[dict]:
        return self._state.get("models", {}).get(model_name, {}).get(version)

    def get_stable_version(self, model_name: str) -> str:
        return str(self._state.get("stable_versions", {}).get(model_name, "") or "")

    def stable_model(self, model_name: str) -> Optional[dict]:
        version = self.get_stable_version(model_name)
        if not version:
            return None
        return self.get_model(model_name, version)

    def events(self, limit: int = 20) -> List[dict]:
        return list(reversed(self._state.get("events", [])[-limit:]))

    def summary(self) -> dict:
        models = self.list_models()
        stable_versions = dict(self._state.get("stable_versions", {}))
        return {
            "manifest_count": len(self.list_manifests()),
            "model_count": len(models),
            "stable_count": len(stable_versions),
            "stable_versions": stable_versions,
            "latest_models": models[-10:],
        }

    def _append_event(self, event: dict) -> None:
        self._state.setdefault("events", []).append(event)


class ModelGovernanceService:
    """模型治理服务。"""

    def __init__(self, store: Optional[ModelGovernanceStore] = None) -> None:
        self.store = store or ModelGovernanceStore()

    def register_feature_manifest(
        self,
        name: str,
        features: Iterable[str],
        *,
        version: str = "v1",
        description: str = "",
        source: str = "",
        meta: Optional[Dict[str, Any]] = None,
    ) -> dict:
        manifest = build_feature_manifest(
            name,
            features,
            version=version,
            description=description,
            source=source,
            meta=meta,
        )
        return self.store.upsert_manifest(manifest)

    def register_model(
        self,
        model_name: str,
        version: Any,
        *,
        status: str = "draft",
        artifact_path: str = "",
        metrics: Optional[Dict[str, Any]] = None,
        thresholds: Optional[Dict[str, Any]] = None,
        feature_manifest: Optional[dict] = None,
        notes: str = "",
    ) -> dict:
        if hasattr(feature_manifest, "to_dict") and callable(getattr(feature_manifest, "to_dict")):
            feature_manifest = feature_manifest.to_dict()
        record = ModelRecord(
            model_name=model_name,
            version=str(version),
            status=status,
            artifact_path=artifact_path,
            metrics=dict(metrics or {}),
            thresholds=dict(thresholds or {}),
            feature_manifest=dict(feature_manifest or {}),
            notes=notes,
        )
        return self.store.upsert_model(record)

    def evaluate_release(
        self,
        model_name: str,
        version: Any,
        *,
        metrics: Optional[Dict[str, Any]] = None,
        thresholds: Optional[Dict[str, Any]] = None,
    ) -> dict:
        version_str = str(version)
        record = self.store.get_model(model_name, version_str)
        current_metrics = dict(metrics or (record or {}).get("metrics", {}) or {})
        current_thresholds = dict(thresholds or (record or {}).get("thresholds", {}) or {})

        if not current_thresholds:
            decision = ReleaseDecision(
                model_name=model_name,
                version=version_str,
                decision="blocked",
                ok=False,
                score=0.0,
                reasons=["no thresholds configured"],
                metrics=current_metrics,
                thresholds=current_thresholds,
            )
            if record is not None:
                self.store.update_model(
                    model_name,
                    version_str,
                    status="blocked",
                    last_decision=decision.to_dict(),
                    metrics=current_metrics,
                    thresholds=current_thresholds,
                )
            return decision.to_dict()

        checks = _evaluate_metrics(current_metrics, current_thresholds)
        if not checks:
            decision = ReleaseDecision(
                model_name=model_name,
                version=version_str,
                decision="blocked",
                ok=False,
                score=0.0,
                reasons=["no comparable metrics"],
                metrics=current_metrics,
                thresholds=current_thresholds,
            )
        else:
            passed = [check for check in checks if check["passed"]]
            score = round(len(passed) / len(checks), 4)
            ok = len(passed) == len(checks)
            decision = ReleaseDecision(
                model_name=model_name,
                version=version_str,
                decision="approved" if ok else "blocked",
                ok=ok,
                score=score,
                reasons=[check["reason"] for check in checks if not check["passed"]] or ["all checks passed"],
                metrics=current_metrics,
                thresholds=current_thresholds,
            )

        if record is not None:
            self.store.update_model(
                model_name,
                version_str,
                status="stable" if decision.ok else "blocked",
                last_decision=decision.to_dict(),
                metrics=current_metrics,
                thresholds=current_thresholds,
            )
        return decision.to_dict()

    def promote(
        self,
        model_name: str,
        version: Any,
        *,
        metrics: Optional[Dict[str, Any]] = None,
        thresholds: Optional[Dict[str, Any]] = None,
    ) -> dict:
        """通过评估后将模型标记为稳定版本。"""
        decision = self.evaluate_release(
            model_name,
            version,
            metrics=metrics,
            thresholds=thresholds,
        )
        if not decision.get("ok"):
            return {
                "ok": False,
                "decision": decision,
                "record": self.store.get_model(model_name, str(version)),
            }

        records = self.store.list_models(model_name)
        for record in records:
            if record.get("model_name") != model_name:
                continue
            if str(record.get("version")) == str(version):
                continue
            if record.get("status") == "stable":
                self.store.update_model(model_name, str(record.get("version")), status="archived")

        promoted = self.store.update_model(
            model_name,
            str(version),
            status="stable",
            last_decision=decision,
        )
        return {
            "ok": True,
            "decision": decision,
            "record": promoted,
        }

    def rollback(self, model_name: str) -> dict:
        """回滚到最近稳定版本。"""
        stable = self.store.stable_model(model_name)
        if stable is None:
            return {
                "ok": False,
                "decision": {
                    "decision": "blocked",
                    "reason": "no stable version available",
                },
                "record": None,
            }

        return {
            "ok": True,
            "decision": {
                "decision": "rolled_back",
                "reason": "restored latest stable version",
            },
            "record": stable,
        }

    def get_status(self, model_name: Optional[str] = None) -> dict:
        """获取模型治理状态。"""
        summary = self.store.summary()
        models = self.store.list_models(model_name)
        manifests = self.store.list_manifests()
        if model_name:
            models = [item for item in models if item.get("model_name") == model_name]
            stable_version = self.store.get_stable_version(model_name)
            summary = {
                **summary,
                "model_count": len(models),
                "stable_count": 1 if stable_version else 0,
            }
        else:
            stable_version = ""
        latest = models[-5:]
        return {
            "ok": True,
            "summary": f"已加载 {len(models)} 条模型记录。" if models else "暂无模型治理记录。",
            "data_source": "model_governance",
            "data": {
                "model_name": model_name or "",
                "stable_version": stable_version,
                "models": models,
                "manifests": manifests,
                "summary": summary,
                "recent_events": self.store.events(20),
                "latest_records": latest,
            },
            "meta": {
                "generated_at": _utcnow(),
                "model_name": model_name or "",
            },
        }


def _evaluate_metrics(metrics: Dict[str, Any], thresholds: Dict[str, Any]) -> List[dict]:
    checks: List[dict] = []
    for metric_name, threshold in thresholds.items():
        if metric_name not in metrics:
            checks.append(
                {
                    "metric": metric_name,
                    "passed": False,
                    "reason": f"missing metric: {metric_name}",
                    "metric_value": None,
                    "threshold": threshold,
                }
            )
            continue

        value = metrics.get(metric_name)
        passed, reason = _check_threshold(value, threshold, metric_name)
        checks.append(
            {
                "metric": metric_name,
                "passed": passed,
                "reason": reason,
                "metric_value": value,
                "threshold": threshold,
            }
        )
    return checks


def _check_threshold(value: Any, threshold: Any, metric_name: str) -> tuple[bool, str]:
    try:
        numeric_value = float(value)
    except Exception:
        return False, f"metric {metric_name} is not numeric"

    if isinstance(threshold, dict):
        if "min" in threshold and numeric_value < float(threshold["min"]):
            return False, f"{metric_name} below min {threshold['min']}"
        if "max" in threshold and numeric_value > float(threshold["max"]):
            return False, f"{metric_name} above max {threshold['max']}"
        if "greater_equal" in threshold and numeric_value < float(threshold["greater_equal"]):
            return False, f"{metric_name} below greater_equal {threshold['greater_equal']}"
        if "less_equal" in threshold and numeric_value > float(threshold["less_equal"]):
            return False, f"{metric_name} above less_equal {threshold['less_equal']}"
        return True, f"{metric_name} passed"

    try:
        numeric_threshold = float(threshold)
    except Exception:
        return False, f"invalid threshold for {metric_name}"

    if numeric_value < numeric_threshold:
        return False, f"{metric_name} below threshold {numeric_threshold}"
    return True, f"{metric_name} passed"


_DEFAULT_MODEL_GOVERNANCE_SERVICE: Optional[ModelGovernanceService] = None


def get_model_governance_service() -> ModelGovernanceService:
    """获取默认模型治理服务。"""
    global _DEFAULT_MODEL_GOVERNANCE_SERVICE
    if _DEFAULT_MODEL_GOVERNANCE_SERVICE is None:
        _DEFAULT_MODEL_GOVERNANCE_SERVICE = ModelGovernanceService()
    return _DEFAULT_MODEL_GOVERNANCE_SERVICE
