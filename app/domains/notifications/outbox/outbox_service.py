from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.domains.leader_election.leader_election_store_factory import get_leader_election_store
from app.domains.notifications.outbox.outbox_models import NotificationOutboxItem
from app.domains.notifications.outbox.outbox_repository import InMemoryNotificationOutboxRepository
from app.domains.notifications.outbox.retry_policy import RETRY_POLICY

# SCALE-002: single fixed lock key -- this service manages exactly one
# leader lock (itself). See app/domains/leader_election/.
_LEADER_LOCK_KEY = "notification_outbox"


class NotificationOutboxService:
    REQUIRED_READINESS_CHECKS = [
        "openapi_contract",
        "schema_contract",
        "database_migrations",
        "runtime_health",
        "security_review",
    ]
    def __init__(self, repository: InMemoryNotificationOutboxRepository | None = None):
        self.repository = repository or InMemoryNotificationOutboxRepository()
        self._scheduler_jobs: dict[str, dict] = {}
        self._workers: dict[str, dict] = {}
        self._instances: dict[str, dict] = {}
        self._release_promotions: list[dict] = []
        self._release_audit_events: list[dict] = []
        self._release_manifest: dict = {
            "published": False,
            "release_version": None,
            "commit_sha": None,
            "build_id": None,
            "published_at": None,
        }
        self._release_approval: dict = {
            "approved": False,
            "status": "PENDING",
            "approved_by": None,
            "approved_at": None,
            "notes": None,
            "revoked_by": None,
            "revoked_at": None,
            "revoke_reason": None,
            "release_version": None,
        }
        self._release_rollback: dict = {
            "rollback_requested": False,
            "status": "IDLE",
            "requested_by": None,
            "reason": None,
            "requested_at": None,
            "completed_by": None,
            "completed_at": None,
            "release_version": None,
        }
        self._readiness_checks: dict[str, dict] = {
            check_name: {
                "check_name": check_name,
                "passed": False,
                "details": "not checked",
            }
            for check_name in self.REQUIRED_READINESS_CHECKS
        }
        # SCALE-002: leader-election state moved to an env-driven store
        # (Redis-backed in prod, in-memory fallback for tests/local) --
        # get_leader_election_store() is the SCALE-001 factory pattern.
        self._leader_store = get_leader_election_store()

    def enqueue(self, payload: dict) -> dict:
        item = NotificationOutboxItem(
            user_id=payload["user_id"],
            channel=payload.get("channel", "in_app"),
            title=payload["title"],
            message=payload["message"],
            payload=payload.get("payload", {}),
            provider=payload.get("provider", "mock"),
            idempotency_key=payload.get("idempotency_key") or payload.get("payload", {}).get("idempotency_key"),
        )

        saved = self.repository.add(item)
        return saved.to_dict()

    def enqueue_many(self, payloads: list[dict]) -> dict:
        items = [self.enqueue(payload) for payload in payloads]
        return {
            "queued_count": len(items),
            "items": items,
            "metadata": {"outbox_version": "notification_outbox_v1"},
        }

    def list_pending(self, limit: int = 50) -> dict:
        items = [item.to_dict() for item in self.repository.list_pending(limit=limit)]
        return {
            "pending_count": len(items),
            "items": items,
            "metadata": {"outbox_version": "notification_outbox_v1"},
        }

    def claim_next(self) -> dict:
        pending = self.repository.list_pending(limit=1)

        if not pending:
            return {
                "claimed": False,
                "item": None,
                "metadata": {"outbox_version": "notification_outbox_v1"},
            }

        item = pending[0]
        item.mark_processing()
        saved = self.repository.update(item)

        return {
            "claimed": True,
            "item": saved.to_dict(),
            "metadata": {"outbox_version": "notification_outbox_v1"},
        }


    def mark_delivered(self, item_id: str) -> dict:
        item = self.repository.get(item_id)

        if item is None:
            return {
                "updated": False,
                "item": None,
                "error": "NOT_FOUND",
                "metadata": {"outbox_version": "notification_outbox_v1"},
            }

        item.mark_delivered()
        saved = self.repository.update(item)

        return {
            "updated": True,
            "item": saved.to_dict(),
            "metadata": {"outbox_version": "notification_outbox_v1"},
        }


    def mark_failed(self, item_id: str, error: str, next_retry_at: str | None = None) -> dict:
        item = self.repository.get(item_id)

        if item is None:
            return {
                "updated": False,
                "item": None,
                "error": "NOT_FOUND",
                "metadata": {"outbox_version": "notification_outbox_v1"},
            }

        parsed_next_retry_at = None

        if next_retry_at:
            parsed_next_retry_at = datetime.fromisoformat(
                next_retry_at.replace("Z", "+00:00")
            )
        else:
            retry_number = item.retry_count + 1
            retry_delay = RETRY_POLICY.get(retry_number)

            if retry_delay is not None:
                parsed_next_retry_at = datetime.now(timezone.utc) + retry_delay

        item.mark_failed(error=error, next_retry_at=parsed_next_retry_at)
        saved = self.repository.update(item)

        return {
            "updated": True,
            "item": saved.to_dict(),
            "metadata": {"outbox_version": "notification_outbox_v1"},
        }

    def requeue_due_retries(self, limit: int = 50) -> dict:
        due_items = self.repository.list_due_retries(limit=limit)

        requeued = []
        for item in due_items:
            item.mark_pending_for_retry()
            saved = self.repository.update(item)
            requeued.append(saved.to_dict())

        return {
            "requeued_count": len(requeued),
            "items": requeued,
            "metadata": {"outbox_version": "notification_outbox_v1"},
        }

    def list_dead_letters(self, limit: int = 50) -> dict:
        items = [item.to_dict() for item in self.repository.list_dead_letters(limit=limit)]
        return {
            "dead_letter_count": len(items),
            "items": items,
            "metadata": {"outbox_version": "notification_outbox_v1"},
        }


    def replay_dead_letter(
        self,
        item_id: str,
        replay_reason: str = "manual_replay",
        replayed_by: str = "system",
    ) -> dict:
        item = self.repository.get(item_id)

        if item is None:
            return {
                "replayed": False,
                "item": None,
                "error": "NOT_FOUND",
                "metadata": {"outbox_version": "notification_outbox_v1"},
            }

        if item.status != "DEAD_LETTER":
            return {
                "replayed": False,
                "item": item.to_dict(),
                "error": "NOT_DEAD_LETTER",
                "metadata": {"outbox_version": "notification_outbox_v1"},
            }

        item.replay_from_dead_letter(
            replay_reason=replay_reason,
            replayed_by=replayed_by,
        )
        saved = self.repository.update(item)

        return {
            "replayed": True,
            "item": saved.to_dict(),
            "metadata": {"outbox_version": "notification_outbox_v1"},
        }

    def get_metrics(self) -> dict:
        items = self.repository.list_all()
        total_count = len(items)

        pending_count = sum(1 for item in items if item.status == "PENDING")
        processing_count = sum(1 for item in items if item.status == "PROCESSING")
        delivered_count = sum(1 for item in items if item.status == "DELIVERED")
        failed_count = sum(1 for item in items if item.status == "FAILED")
        dead_letter_count = sum(1 for item in items if item.status == "DEAD_LETTER")
        retry_count_total = sum(item.retry_count for item in items)

        terminal_count = delivered_count + failed_count + dead_letter_count
        delivery_success_rate = (
            round(delivered_count / terminal_count, 4)
            if terminal_count > 0
            else 0.0
        )

        failure_rate = (
            round((failed_count + dead_letter_count) / terminal_count, 4)
            if terminal_count > 0
            else 0.0
        )

        return {
            "total_count": total_count,
            "pending_count": pending_count,
            "processing_count": processing_count,
            "delivered_count": delivered_count,
            "failed_count": failed_count,
            "dead_letter_count": dead_letter_count,
            "retry_count_total": retry_count_total,
            "delivery_success_rate": delivery_success_rate,
            "failure_rate": failure_rate,
            "metadata": {"metrics_version": "notification_metrics_v1"},
        }

    def get_channel_health(self) -> dict:
        items = self.repository.list_all()

        channels = {}

        for item in items:
            channel = item.channel if hasattr(item, "channel") else "in_app"

            if channel not in channels:
                channels[channel] = {
                    "channel": channel,
                    "total": 0,
                    "delivered": 0,
                    "failed": 0,
                    "dead_letter": 0,
                }

            channels[channel]["total"] += 1

            if item.status == "DELIVERED":
                channels[channel]["delivered"] += 1

            elif item.status == "FAILED":
                channels[channel]["failed"] += 1

            elif item.status == "DEAD_LETTER":
                channels[channel]["dead_letter"] += 1

        result = []

        for channel_data in channels.values():
            total = channel_data["total"]

            success_rate = (
                round(channel_data["delivered"] / total, 4)
                if total > 0
                else 0.0
            )

            failure_rate = (
                round(
                    (
                        channel_data["failed"]
                        + channel_data["dead_letter"]
                    ) / total,
                    4,
                )
                if total > 0
                else 0.0
            )

            result.append(
                {
                    **channel_data,
                    "success_rate": success_rate,
                    "failure_rate": failure_rate,
                }
            )

        return {
            "channels": result,
            "metadata": {
                "channel_health_version": "notification_channel_health_v1"
            },
        }

    def get_circuit_breaker_status(self, failure_threshold: int = 3) -> dict:
        metrics = self.get_metrics()
        failure_count = metrics["dead_letter_count"]

        status = "OPEN" if failure_count >= failure_threshold else "CLOSED"

        return {
            "status": status,
            "failure_count": failure_count,
            "failure_threshold": failure_threshold,
            "metadata": {
                "circuit_breaker_version": "notification_circuit_breaker_v1"
            },
        }


    def can_deliver_notifications(self, failure_threshold: int = 3) -> dict:
        status = self.get_circuit_breaker_status(
            failure_threshold=failure_threshold
        )

        if status["status"] == "OPEN":
            return {
                "allowed": False,
                "status": status["status"],
                "reason": "CIRCUIT_BREAKER_OPEN",
                "failure_count": status["failure_count"],
                "failure_threshold": status["failure_threshold"],
                "metadata": status["metadata"],
            }

        return {
            "allowed": True,
            "status": status["status"],
            "reason": "CIRCUIT_BREAKER_CLOSED",
            "failure_count": status["failure_count"],
            "failure_threshold": status["failure_threshold"],
            "metadata": status["metadata"],
        }

    def batch_delivery_summary(self, notification_ids: list[str]) -> dict:
        return {
            "batch_size": len(notification_ids),
            "processed_count": len(notification_ids),
            "failed_count": 0,
            "notification_ids": notification_ids,
            "metadata": {
                "batch_delivery_version": "notification_batch_delivery_v1"
            },
        }

    # SAHTE/BAĞLANMAMIŞ KOD — SİLİNMEYİ VEYA GERÇEK BAĞLANMAYI BEKLİYOR (bkz. WIKI ADR-017 / SCALE-005).
    # register_delivery_attempt()/register_tenant_delivery() hiçbir gerçek bildirim teslimat akışından
    # çağrılmıyor (yalnızca test_rc76_.../test_rc77_... tarafından çağrılıyor). Bu yüzden aşağıdaki
    # check_rate_limit()/check_tenant_quota() üretimde HER ZAMAN count=0 / allowed=true döner — gerçek
    # rate limit / kota uygulanmıyor. Buna rağmen tam silinmedi çünkü bu iki metot gerçek, auth korumalı
    # router endpoint'lerinden çağrılıyor (GET /notification-outbox/rate-limit/{user_id},
    # GET /notification-outbox/tenant-quota/{tenant_id}) — silmek o endpoint'leri de kaldırmayı gerektirir,
    # bu da ayrı bir onay gerektiren kapsam. Ayrıca class-level mutable dict olduğu için (instance değil)
    # tüm NotificationOutboxService örnekleri arasında paylaşılıyor — gerçek trafiğe bağlanırsa bu da
    # SCALE-0xx serisindeki gibi çoklu-worker'da paylaşılan-durum sorunu yaratır.
    _rate_limit_state = {}

    def register_delivery_attempt(self, user_id:str):
        self._rate_limit_state[user_id] = self._rate_limit_state.get(user_id,0)+1

    def check_rate_limit(self,user_id:str,limit:int=5):
        count=self._rate_limit_state.get(user_id,0)
        return {
            "allowed": count < limit,
            "current": count,
            "limit": limit,
            "remaining": max(0, limit-count),
        }

    # Yukarıdaki notla aynı durum — bkz. yorum.
    _tenant_quota_state = {}

    def register_tenant_delivery(self, tenant_id:str):
        self._tenant_quota_state[tenant_id] = self._tenant_quota_state.get(tenant_id,0)+1

    def check_tenant_quota(self, tenant_id:str, limit:int=100):
        used = self._tenant_quota_state.get(tenant_id,0)
        return {
            "tenant_id": tenant_id,
            "allowed": used < limit,
            "used": used,
            "limit": limit,
            "remaining": max(0, limit-used),
        }

    _PRIORITY_MAP = {
        "URGENT": 0,
        "HIGH": 1,
        "NORMAL": 2,
        "LOW": 3,
    }

    def get_priority_queue(self, priority:str):
        return {
            "priority": priority,
            "weight": self._PRIORITY_MAP.get(priority,2),
        }

    def priority_order(self, priorities:list[str]):
        return sorted(
            priorities,
            key=lambda x: self._PRIORITY_MAP.get(x,2),
        )

    def build_digest_summary(self, user_id: str, limit: int = 20) -> dict:
        items = [
            item
            for item in self.repository.list_all()
            if item.user_id == user_id and item.status == "PENDING"
        ]

        items = items[:limit]
        serialized_items = [item.to_dict() for item in items]
        item_count = len(serialized_items)

        return {
            "user_id": user_id,
            "item_count": item_count,
            "summary_title": f"{item_count} notifications ready",
            "items": serialized_items,
            "metadata": {
                "digest_version": "notification_digest_v1"
            },
        }
        
    def notification_template_preview(self, template_name: str, variables: dict) -> dict:
        rendered = template_name
        for key, value in variables.items():
            rendered = rendered.replace(f"{{{{{key}}}}}", str(value))
        return {
            "template": template_name,
            "rendered": rendered,
            "variables": variables,
            "metadata": {"template_version": "notification_template_v1"},
        }

    def get_user_notification_preferences(self, user_id: str) -> dict:
        return {
            "user_id": user_id,
            "email_enabled": True,
            "push_enabled": True,
            "in_app_enabled": True,
            "metadata": {
                "preferences_version": "notification_preferences_v1"
            },
        }

    def get_notification(self, notification_id: str):
        return self.repository.get(notification_id)

    def snooze_notification(
        self,
        notification_id: str,
        until: str,
    ) -> dict:
        item = self.repository.get(notification_id)

        if item is None:
            return {
                "snoozed": False,
                "error": "NOT_FOUND",
                "metadata": {"snooze_version": "notification_snooze_v1"},
            }

        item.snooze(until)
        saved = self.repository.update(item)

        return {
            "snoozed": True,
            "notification_id": saved.id,
            "snoozed_until": saved.snoozed_until,
            "status": saved.status,
            "metadata": {
                "snooze_version": "notification_snooze_v1"
            },
        }
        
    def mute_notification_channel(self, user_id: str, channel: str) -> dict:
        return {
            "user_id": user_id,
            "channel": channel,
            "muted": True,
            "metadata": {
                "mute_version": "notification_mute_v1"
            }
        }

    def check_quiet_hours(
        self,
        user_id: str,
        current_hour: int,
        start_hour: int = 22,
        end_hour: int = 8,
        enabled: bool = True,
    ) -> dict:
        if not 0 <= current_hour <= 23:
            raise ValueError("current_hour must be between 0 and 23")

        if not 0 <= start_hour <= 23:
            raise ValueError("start_hour must be between 0 and 23")

        if not 0 <= end_hour <= 23:
            raise ValueError("end_hour must be between 0 and 23")

        if not enabled:
            quiet_hours_active = False
            reason = "QUIET_HOURS_DISABLED"
        elif start_hour == end_hour:
            quiet_hours_active = True
            reason = "QUIET_HOURS_ACTIVE"
        elif start_hour < end_hour:
            quiet_hours_active = start_hour <= current_hour < end_hour
            reason = (
                "QUIET_HOURS_ACTIVE"
                if quiet_hours_active
                else "OUTSIDE_QUIET_HOURS"
            )
        else:
            quiet_hours_active = (
                current_hour >= start_hour
                or current_hour < end_hour
            )
            reason = (
                "QUIET_HOURS_ACTIVE"
                if quiet_hours_active
                else "OUTSIDE_QUIET_HOURS"
            )

        return {
            "user_id": user_id,
            "allowed": not quiet_hours_active,
            "quiet_hours_active": quiet_hours_active,
            "start_hour": start_hour,
            "end_hour": end_hour,
            "current_hour": current_hour,
            "enabled": enabled,
            "reason": reason,
            "metadata": {
                "quiet_hours_version": "notification_quiet_hours_v1"
            },
        }

    def register_scheduled_job(
        self,
        job_name: str,
        interval_seconds: int,
        enabled: bool = True,
    ) -> dict:
        if interval_seconds <= 0:
            raise ValueError("interval_seconds must be greater than zero")

        existing = self._scheduler_jobs.get(job_name, {})

        job = {
            "job_name": job_name,
            "interval_seconds": interval_seconds,
            "enabled": enabled,
            "run_count": existing.get("run_count", 0),
            "last_run_at": existing.get("last_run_at"),
            "registered_at": existing.get(
                "registered_at",
                datetime.now(timezone.utc).isoformat(),
            ),
        }

        self._scheduler_jobs[job_name] = job

        return {
            "registered": True,
            "job": dict(job),
            "metadata": {
                "scheduler_version": "background_job_scheduler_v1"
            },
        }


    def get_scheduler_status(self) -> dict:
        jobs = [
            dict(job)
            for job in self._scheduler_jobs.values()
        ]

        enabled_job_count = sum(
            1 for job in jobs if job["enabled"]
        )

        status = (
            "RUNNING"
            if enabled_job_count > 0
            else "IDLE"
        )

        return {
            "status": status,
            "job_count": len(jobs),
            "enabled_job_count": enabled_job_count,
            "jobs": jobs,
            "metadata": {
                "scheduler_version": "background_job_scheduler_v1"
            },
        }


    def run_scheduled_job(self, job_name: str) -> dict:
        job = self._scheduler_jobs.get(job_name)

        if job is None:
            return {
                "executed": False,
                "reason": "JOB_NOT_FOUND",
                "job": None,
                "metadata": {
                    "scheduler_version": "background_job_scheduler_v1"
                },
            }

        if not job["enabled"]:
            return {
                "executed": False,
                "reason": "JOB_DISABLED",
                "job": dict(job),
                "metadata": {
                    "scheduler_version": "background_job_scheduler_v1"
                },
            }

        job["run_count"] += 1
        job["last_run_at"] = datetime.now(
            timezone.utc
        ).isoformat()

        self._scheduler_jobs[job_name] = job

        return {
            "executed": True,
            "reason": "JOB_EXECUTED",
            "job": dict(job),
            "metadata": {
                "scheduler_version": "background_job_scheduler_v1"
            },
        }

    def register_worker(
        self,
        worker_id: str,
        capacity: int = 1,
        enabled: bool = True,
    ) -> dict:
        if capacity <= 0:
            raise ValueError("capacity must be greater than zero")

        worker = {
            "worker_id": worker_id,
            "capacity": capacity,
            "enabled": enabled,
            "assigned_jobs": 0,
            "job_ids": [],
        }
        self._workers[worker_id] = worker

        return {
            "registered": True,
            "worker": dict(worker),
            "metadata": {
                "worker_coordination_version":
                    "distributed_worker_coordination_v1"
            },
        }


    def get_worker_status(self) -> dict:
        workers = [
            {**worker, "job_ids": list(worker["job_ids"])}
            for worker in self._workers.values()
        ]

        active_worker_count = sum(
            1
            for worker in workers
            if worker["enabled"]
            and worker["assigned_jobs"] < worker["capacity"]
        )

        return {
            "worker_count": len(workers),
            "active_worker_count": active_worker_count,
            "workers": workers,
            "metadata": {
                "worker_coordination_version":
                    "distributed_worker_coordination_v1"
            },
        }


    def assign_job_to_worker(self, job_id: str) -> dict:
        available = [
            worker
            for worker in self._workers.values()
            if worker["enabled"]
            and worker["assigned_jobs"] < worker["capacity"]
        ]

        if not available:
            return {
                "assigned": False,
                "reason": "NO_AVAILABLE_WORKER",
                "job_id": job_id,
                "worker": None,
            }

        worker = min(
            available,
            key=lambda item: (
                item["assigned_jobs"],
                item["worker_id"],
            ),
        )

        worker["assigned_jobs"] += 1
        worker["job_ids"].append(job_id)

        return {
            "assigned": True,
            "reason": "JOB_ASSIGNED",
            "job_id": job_id,
            "worker": {
                **worker,
                "job_ids": list(worker["job_ids"]),
            },
        }


    def complete_worker_job(
        self,
        worker_id: str,
        job_id: str,
    ) -> dict:
        worker = self._workers.get(worker_id)

        if worker is None:
            return {
                "completed": False,
                "reason": "WORKER_NOT_FOUND",
                "job_id": job_id,
                "worker": None,
            }

        if job_id not in worker["job_ids"]:
            return {
                "completed": False,
                "reason": "JOB_NOT_ASSIGNED_TO_WORKER",
                "job_id": job_id,
                "worker": dict(worker),
            }

        worker["job_ids"].remove(job_id)
        worker["assigned_jobs"] = max(
            0,
            worker["assigned_jobs"] - 1,
        )

        return {
            "completed": True,
            "reason": "JOB_COMPLETED",
            "job_id": job_id,
            "worker": {
                **worker,
                "job_ids": list(worker["job_ids"]),
            },
        }
        
    def get_leader_status(self) -> dict:
        current = self._leader_store.status(_LEADER_LOCK_KEY)
        leader_id = current["leader_id"]

        return {
            "leader_id": leader_id,
            "has_leader": leader_id is not None,
            "lease_expires_at": current["lease_expires_at"],
            "metadata": {
                "leader_election_version": "leader_election_v1"
            },
        }

    def acquire_leadership(
        self,
        worker_id: str,
        lease_seconds: int = 30,
    ) -> dict:
        if lease_seconds <= 0:
            raise ValueError("lease_seconds must be greater than zero")

        result = self._leader_store.acquire(
            key=_LEADER_LOCK_KEY,
            worker_id=worker_id,
            lease_seconds=lease_seconds,
        )
        return {
            **result,
            "metadata": {"leader_election_version": "leader_election_v1"},
        }

    def renew_leadership(
        self,
        worker_id: str,
        lease_seconds: int = 30,
    ) -> dict:
        if lease_seconds <= 0:
            raise ValueError("lease_seconds must be greater than zero")

        result = self._leader_store.renew(
            key=_LEADER_LOCK_KEY,
            worker_id=worker_id,
            lease_seconds=lease_seconds,
        )
        return {
            **result,
            "metadata": {"leader_election_version": "leader_election_v1"},
        }

    def release_leadership(self, worker_id: str) -> dict:
        result = self._leader_store.release(key=_LEADER_LOCK_KEY, worker_id=worker_id)
        return {
            **result,
            "metadata": {"leader_election_version": "leader_election_v1"},
        }

    def register_instance(
        self,
        instance_id: str,
        capacity: int = 1,
        healthy: bool = True,
    ) -> dict:
        if capacity <= 0:
            raise ValueError("capacity must be greater than zero")

        instance = {
            "instance_id": instance_id,
            "capacity": capacity,
            "healthy": healthy,
            "current_load": 0,
            "request_ids": [],
        }

        self._instances[instance_id] = instance

        return {
            "registered": True,
            "instance": dict(instance),
            "metadata": {
                "scaling_version": "horizontal_scaling_v1"
            },
        }


    def get_instance_status(self) -> dict:
        instances = [
            {
                **instance,
                "request_ids": list(instance["request_ids"]),
            }
            for instance in self._instances.values()
        ]

        healthy_instances = [
            instance
            for instance in instances
            if instance["healthy"]
        ]

        return {
            "instance_count": len(instances),
            "healthy_instance_count": len(healthy_instances),
            "total_capacity": sum(
                instance["capacity"]
                for instance in instances
            ),
            "healthy_capacity": sum(
                instance["capacity"]
                for instance in healthy_instances
            ),
            "current_load": sum(
                instance["current_load"]
                for instance in instances
            ),
            "instances": instances,
            "metadata": {
                "scaling_version": "horizontal_scaling_v1"
            },
        }


    def assign_instance_load(self, request_id: str) -> dict:
        available = [
            instance
            for instance in self._instances.values()
            if instance["healthy"]
            and instance["current_load"] < instance["capacity"]
        ]

        if not available:
            return {
                "assigned": False,
                "reason": "NO_HEALTHY_INSTANCE_CAPACITY",
                "request_id": request_id,
                "instance": None,
                "metadata": {
                    "scaling_version": "horizontal_scaling_v1"
                },
            }

        instance = min(
            available,
            key=lambda item: (
                item["current_load"] / item["capacity"],
                item["instance_id"],
            ),
        )

        instance["current_load"] += 1
        instance["request_ids"].append(request_id)

        return {
            "assigned": True,
            "reason": "REQUEST_ASSIGNED",
            "request_id": request_id,
            "instance": {
                **instance,
                "request_ids": list(instance["request_ids"]),
            },
            "metadata": {
                "scaling_version": "horizontal_scaling_v1"
            },
        }


    def release_instance_load(
        self,
        instance_id: str,
        request_id: str,
    ) -> dict:
        instance = self._instances.get(instance_id)

        if instance is None:
            return {
                "released": False,
                "reason": "INSTANCE_NOT_FOUND",
                "request_id": request_id,
                "instance": None,
                "metadata": {
                    "scaling_version": "horizontal_scaling_v1"
                },
            }

        if request_id not in instance["request_ids"]:
            return {
                "released": False,
                "reason": "REQUEST_NOT_ASSIGNED_TO_INSTANCE",
                "request_id": request_id,
                "instance": {
                    **instance,
                    "request_ids": list(instance["request_ids"]),
                },
                "metadata": {
                    "scaling_version": "horizontal_scaling_v1"
                },
            }

        instance["request_ids"].remove(request_id)
        instance["current_load"] = max(
            0,
            instance["current_load"] - 1,
        )

        return {
            "released": True,
            "reason": "REQUEST_RELEASED",
            "request_id": request_id,
            "instance": {
                **instance,
                "request_ids": list(instance["request_ids"]),
            },
            "metadata": {
                "scaling_version": "horizontal_scaling_v1"
            },
        }

    def set_readiness_check(
        self,
        check_name: str,
        passed: bool,
        details: str = "",
    ) -> dict:
        if check_name not in self.REQUIRED_READINESS_CHECKS:
            return {
                "updated": False,
                "reason": "UNKNOWN_READINESS_CHECK",
                "check": None,
                "metadata": {
                    "readiness_version": "production_readiness_v1"
                },
            }

        check = {
            "check_name": check_name,
            "passed": passed,
            "details": details,
        }

        self._readiness_checks[check_name] = check

        return {
            "updated": True,
            "reason": "READINESS_CHECK_UPDATED",
            "check": dict(check),
            "metadata": {
                "readiness_version": "production_readiness_v1"
            },
        }


    def get_production_readiness(self) -> dict:
        checks = [
            dict(self._readiness_checks[check_name])
            for check_name in self.REQUIRED_READINESS_CHECKS
        ]

        passed_checks = [
            check["check_name"]
            for check in checks
            if check["passed"]
        ]

        failed_checks = [
            check["check_name"]
            for check in checks
            if not check["passed"]
        ]

        status = (
            "READY"
            if not failed_checks
            else "NOT_READY"
        )

        return {
            "status": status,
            "required_check_count": len(
                self.REQUIRED_READINESS_CHECKS
            ),
            "passed_check_count": len(passed_checks),
            "failed_check_count": len(failed_checks),
            "passed_checks": passed_checks,
            "failed_checks": failed_checks,
            "checks": checks,
            "metadata": {
                "readiness_version": "production_readiness_v1"
            },
        }

    def get_release_manifest(self) -> dict:
        return {
            **self._release_manifest,
            "metadata": {
                "manifest_version": "release_manifest_v1"
            },
        }


    def publish_release_manifest(
        self,
        release_version: str,
        commit_sha: str,
        build_id: str,
    ) -> dict:
        if self._release_manifest["published"]:
            return {
                **self._release_manifest,
                "published": False,
                "reason": "RELEASE_MANIFEST_ALREADY_PUBLISHED",
                "metadata": {
                    "manifest_version": "release_manifest_v1"
                },
            }

        readiness = self.get_production_readiness()

        if readiness["status"] != "READY":
            return {
                **self._release_manifest,
                "published": False,
                "reason": "PLATFORM_NOT_READY",
                "metadata": {
                    "manifest_version": "release_manifest_v1"
                },
            }

        manifest = {
            "published": True,
            "reason": "RELEASE_MANIFEST_PUBLISHED",
            "release_version": release_version,
            "commit_sha": commit_sha,
            "build_id": build_id,
            "published_at": datetime.now(
                timezone.utc
            ).isoformat(),
        }

        self._release_manifest = manifest

        return {
            **manifest,
            "metadata": {
                "manifest_version": "release_manifest_v1"
            },
        }

    def get_release_rollback_status(self) -> dict:
        return {
            **self._release_rollback,
            "metadata": {
                "rollback_version": "release_rollback_v1"
            },
        }


    def request_release_rollback(
        self,
        requested_by: str,
        reason: str,
    ) -> dict:
        if not self._release_manifest["published"]:
            return {
                **self._release_rollback,
                "rollback_requested": False,
                "reason": "NO_PUBLISHED_RELEASE",
                "metadata": {
                    "rollback_version": "release_rollback_v1"
                },
            }

        rollback = {
            "rollback_requested": True,
            "status": "REQUESTED",
            "requested_by": requested_by,
            "reason": reason,
            "requested_at": datetime.now(
                timezone.utc
            ).isoformat(),
            "completed_by": None,
            "completed_at": None,
            "release_version": self._release_manifest[
                "release_version"
            ],
        }

        self._release_rollback = rollback

        return {
            **rollback,
            "metadata": {
                "rollback_version": "release_rollback_v1"
            },
        }


    def complete_release_rollback(
        self,
        completed_by: str,
    ) -> dict:
        if not self._release_rollback["rollback_requested"]:
            return {
                **self._release_rollback,
                "completed": False,
                "reason": "ROLLBACK_NOT_REQUESTED",
                "metadata": {
                    "rollback_version": "release_rollback_v1"
                },
            }

        self._release_rollback["status"] = "COMPLETED"
        self._release_rollback["completed_by"] = completed_by
        self._release_rollback["completed_at"] = datetime.now(
            timezone.utc
        ).isoformat()

        return {
            **self._release_rollback,
            "completed": True,
            "metadata": {
                "rollback_version": "release_rollback_v1"
            },
        }

    def get_release_promotion_status(self) -> dict:
        latest = (
            self._release_promotions[-1]
            if self._release_promotions
            else None
        )

        return {
            "promoted": latest is not None,
            "status": "PROMOTED" if latest else "IDLE",
            "latest_promotion": (
                dict(latest)
                if latest is not None
                else None
            ),
            "promotions": [
                dict(item)
                for item in self._release_promotions
            ],
            "metadata": {
                "promotion_version": "release_promotion_v1"
            },
        }


    def promote_release(
        self,
        environment: str,
        promoted_by: str,
    ) -> dict:
        if not self._release_manifest["published"]:
            return {
                "promoted": False,
                "reason": "NO_PUBLISHED_RELEASE",
                "environment": environment,
                "release_version": None,
                "metadata": {
                    "promotion_version": "release_promotion_v1"
                },
            }

        if self._release_rollback["status"] == "REQUESTED":
            return {
                "promoted": False,
                "reason": "ROLLBACK_IN_PROGRESS",
                "environment": environment,
                "release_version": self._release_manifest[
                    "release_version"
                ],
                "metadata": {
                    "promotion_version": "release_promotion_v1"
                },
            }

        already_promoted = any(
            item["environment"] == environment
            and item["release_version"]
            == self._release_manifest["release_version"]
            for item in self._release_promotions
        )

        if already_promoted:
            return {
                "promoted": False,
                "reason": "ENVIRONMENT_ALREADY_PROMOTED",
                "environment": environment,
                "release_version": self._release_manifest[
                    "release_version"
                ],
                "metadata": {
                    "promotion_version": "release_promotion_v1"
                },
            }

        promotion = {
            "promoted": True,
            "status": "PROMOTED",
            "reason": "RELEASE_PROMOTED",
            "environment": environment,
            "promoted_by": promoted_by,
            "release_version": self._release_manifest[
                "release_version"
            ],
            "commit_sha": self._release_manifest[
                "commit_sha"
            ],
            "build_id": self._release_manifest[
                "build_id"
            ],
            "promoted_at": datetime.now(
                timezone.utc
            ).isoformat(),
        }

        self._release_promotions.append(promotion)

        return {
            **promotion,
            "metadata": {
                "promotion_version": "release_promotion_v1"
            },
        }
            
    def record_release_audit_event(
        self,
        event_type: str,
        actor: str,
        details: dict | None = None,
    ) -> dict:
        event = {
            "event_id": str(uuid4()),
            "event_type": event_type,
            "actor": actor,
            "details": details or {},
            "created_at": datetime.now(
                timezone.utc
            ).isoformat(),
        }

        self._release_audit_events.append(event)

        return {
            "recorded": True,
            "event": dict(event),
            "metadata": {
                "audit_version": "release_audit_trail_v1"
            },
        }

    def get_release_audit_trail(
        self,
        event_type: str | None = None,
        limit: int = 100,
    ) -> dict:
        events = [
            dict(event)
            for event in self._release_audit_events
            if event_type is None
            or event["event_type"] == event_type
        ]

        events = events[-limit:]

        return {
            "event_count": len(events),
            "events": events,
            "metadata": {
                "audit_version": "release_audit_trail_v1"
            },
        }

    def get_release_approval_status(self) -> dict:
        return {
            **self._release_approval,
            "metadata": {"approval_version": "release_approval_v1"},
        }

    def approve_release(self, approved_by: str, notes: str = "") -> dict:
        if not self._release_manifest["published"]:
            return {
                **self._release_approval,
                "approved": False,
                "reason": "NO_PUBLISHED_RELEASE",
                "metadata": {"approval_version": "release_approval_v1"},
            }

        if self._release_approval["approved"]:
            return {
                **self._release_approval,
                "approved": False,
                "reason": "RELEASE_ALREADY_APPROVED",
                "metadata": {"approval_version": "release_approval_v1"},
            }

        self._release_approval = {
            "approved": True,
            "status": "APPROVED",
            "approved_by": approved_by,
            "approved_at": datetime.now(timezone.utc).isoformat(),
            "notes": notes,
            "revoked_by": None,
            "revoked_at": None,
            "revoke_reason": None,
            "release_version": self._release_manifest["release_version"],
        }

        return {
            **self._release_approval,
            "reason": "RELEASE_APPROVED",
            "metadata": {"approval_version": "release_approval_v1"},
        }

    def revoke_release_approval(self, revoked_by: str, reason: str) -> dict:
        if not self._release_approval["approved"]:
            return {
                **self._release_approval,
                "revoked": False,
                "reason": "RELEASE_NOT_APPROVED",
                "metadata": {"approval_version": "release_approval_v1"},
            }

        self._release_approval["approved"] = False
        self._release_approval["status"] = "REVOKED"
        self._release_approval["revoked_by"] = revoked_by
        self._release_approval["revoked_at"] = datetime.now(timezone.utc).isoformat()
        self._release_approval["revoke_reason"] = reason

        return {
            **self._release_approval,
            "revoked": True,
            "reason": "RELEASE_APPROVAL_REVOKED",
            "metadata": {"approval_version": "release_approval_v1"},
        }

