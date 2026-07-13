class AlertNotificationService:
    """
    Stable alert notification orchestration service.

    Design principles:
    - Keep constructor import-safe.
    - Preserve legacy queue payload types.
    - Do JSON/string serialization at API/transport boundary, not inside the domain service.
    - Support method-based and list-attribute queue/repository objects.
    """

    def __init__(self, evaluation_service_or_db, notification_repository=None, queue=None):
        self.db = None
        self.evaluation_service = None
        self.notification_repository = None
        self.rule_repository = None
        self.queue = queue

        if notification_repository is not None:
            self.evaluation_service = evaluation_service_or_db
            self.notification_repository = notification_repository
            return

        self.db = evaluation_service_or_db

    async def evaluate_and_enqueue(
        self,
        *,
        offer_id,
        current_price,
        previous_price=None,
        price_change=None,
    ):
        self._ensure_evaluation_dependencies()

        evaluation = await self.evaluation_service.evaluate_for_offer(
            offer_id=offer_id,
            current_price=current_price,
            previous_price=previous_price,
            price_change=price_change,
        )

        if self.notification_repository is not None:
            queued = []
            for item in evaluation["results"]:
                if not item.get("triggered"):
                    continue

                queued.append(
                    await self._create_notification(
                        {
                            "rule_id": item.get("rule_id"),
                            "offer_id": item.get("offer_id", offer_id),
                            "notification_type": item.get("rule_type"),
                            "status": "PENDING",
                            "payload": {
                                "reason": item.get("reason"),
                                "message": item.get("message"),
                            },
                        }
                    )
                )

            return {
                "offer_id": offer_id,
                "evaluated_count": evaluation.get("evaluated_count", 0),
                "triggered_count": evaluation.get("triggered_count", 0),
                "queued_count": len(queued),
                "queued": queued,
            }

        return await self.enqueue_triggered_evaluations(
            evaluations=evaluation,
            rules_by_id={},
        )

    async def evaluate_and_queue(
        self,
        *,
        offer_id,
        current_price,
        previous_price=None,
        price_change=None,
    ):
        return await self.evaluate_and_enqueue(
            offer_id=offer_id,
            current_price=current_price,
            previous_price=previous_price,
            price_change=price_change,
        )

    async def enqueue_triggered_evaluations(self, *, evaluations: dict, rules_by_id: dict):
        queued = []
        skipped_missing_rule_count = 0
        skipped_untriggered_count = 0

        for item in evaluations.get("results", []):
            if not item.get("triggered"):
                skipped_untriggered_count += 1
                continue

            raw_rule_id = item.get("rule_id")
            rule = rules_by_id.get(raw_rule_id) or rules_by_id.get(str(raw_rule_id))

            if rule is None:
                skipped_missing_rule_count += 1
                continue

            payload = self._build_legacy_notification_payload(item=item, rule=rule)
            queued_item = await self._enqueue_to_queue(payload)
            queued.append(queued_item)

        return {
            "evaluated_count": evaluations.get("evaluated_count", 0),
            "triggered_count": evaluations.get("triggered_count", 0),
            "queued_count": len(queued),
            "skipped_missing_rule_count": skipped_missing_rule_count,
            "skipped_untriggered_count": skipped_untriggered_count,
            "queued": queued,
        }

    def _build_legacy_notification_payload(self, *, item: dict, rule):
        # Preserve domain/native ID types for legacy in-process queue tests/callers.
        rule_id = getattr(rule, "id", item.get("rule_id"))
        offer_id = item.get("offer_id", getattr(rule, "offer_id", None))
        user_id = item.get("user_id", getattr(rule, "user_id", None))
        rule_type = item.get("rule_type", getattr(rule, "rule_type", None))

        payload = {
            "rule_id": rule_id,
            "offer_id": offer_id,
            "notification_type": rule_type,
            "status": "PENDING",
            "message": item.get("message"),
            "payload": {
                "reason": item.get("reason"),
                "message": item.get("message"),
                "rule_type": rule_type,
            },
        }

        if user_id is not None:
            payload["user_id"] = user_id

        return payload

    async def _enqueue_to_queue(self, payload: dict):
        if self.queue is not None:
            return await self._call_queue_or_append(self.queue, payload)

        if self.notification_repository is not None:
            return await self._create_notification(payload)

        self._ensure_notification_repository()
        return await self._create_notification(payload)

    async def _create_notification(self, payload: dict):
        return await self._call_queue_or_append(self.notification_repository, payload)

    async def _call_queue_or_append(self, target, payload: dict):
        method_result = await self._call_first_available_or_none(
            target,
            method_names=["enqueue", "create", "add", "put", "append"],
            payload=payload,
        )

        if method_result is not None:
            return method_result

        appended = self._append_to_first_list_attribute(
            target,
            attribute_names=[
                "items",
                "notifications",
                "queued",
                "queue",
                "pending",
                "pending_notifications",
                "created",
            ],
            payload=payload,
        )

        if appended is not None:
            return appended

        raise AttributeError(
            "Queue/repository target does not expose a supported method "
            "or list attribute. Supported methods: enqueue, create, add, put, append. "
            "Supported list attributes: items, notifications, queued, queue, pending, "
            "pending_notifications, created."
        )

    async def _call_first_available_or_none(self, target, *, method_names: list[str], payload: dict):
        for method_name in method_names:
            method = getattr(target, method_name, None)
            if method is None or not callable(method):
                continue

            try:
                result = method(payload)
            except TypeError:
                result = method(**payload)

            if hasattr(result, "__await__"):
                return await result

            return result if result is not None else payload

        return None

    def _append_to_first_list_attribute(self, target, *, attribute_names: list[str], payload: dict):
        for attribute_name in attribute_names:
            value = getattr(target, attribute_name, None)
            if isinstance(value, list):
                value.append(payload)
                return payload
        return None

    def _ensure_evaluation_dependencies(self):
        if self.evaluation_service is not None:
            return

        if self.rule_repository is None:
            AlertRuleRepository = self._import_first_class(
                [
                    ("app.domains.alerts.rule_repository", "AlertRuleRepository"),
                    ("app.domains.alerts.alert_rule_repository", "AlertRuleRepository"),
                    ("app.domains.alerts.repository", "AlertRuleRepository"),
                    ("app.domains.alerts.db_repository", "AlertRuleRepository"),
                    ("app.domains.alerts.alert_rule_db_repository", "AlertRuleRepository"),
                ],
                friendly_name="AlertRuleRepository",
            )
            self.rule_repository = AlertRuleRepository(self.db)

        AlertEvaluationService = self._import_first_class(
            [
                ("app.domains.alerts.evaluation_service", "AlertEvaluationService"),
                ("app.domains.alerts.alert_evaluation_service", "AlertEvaluationService"),
            ],
            friendly_name="AlertEvaluationService",
        )
        self.evaluation_service = AlertEvaluationService(self.rule_repository)

    def _ensure_notification_repository(self):
        if self.notification_repository is not None:
            return

        PendingNotificationRepository = self._import_first_class(
            [
                ("app.domains.alerts.notification_repository", "PendingNotificationRepository"),
                ("app.domains.alerts.notification_queue_repository", "PendingNotificationRepository"),
                ("app.domains.alerts.pending_notification_repository", "PendingNotificationRepository"),
                ("app.domains.alerts.repository", "PendingNotificationRepository"),
                ("app.domains.alerts.db_repository", "PendingNotificationRepository"),
                ("app.domains.alerts.notification_queue_repository", "NotificationQueueRepository"),
                ("app.domains.alerts.pending_notification_repository", "NotificationQueueRepository"),
                ("app.domains.alerts.repository", "NotificationQueueRepository"),
                ("app.domains.alerts.db_repository", "NotificationQueueRepository"),
            ],
            friendly_name="PendingNotificationRepository/NotificationQueueRepository",
        )
        self.notification_repository = PendingNotificationRepository(self.db)

    def _import_first_class(self, candidates, *, friendly_name: str):
        errors = []

        for module_name, class_name in candidates:
            try:
                module = __import__(module_name, fromlist=[class_name])
                return getattr(module, class_name)
            except (ImportError, AttributeError) as exc:
                errors.append(f"{module_name}.{class_name}: {exc}")

        raise ImportError(
            f"Could not find {friendly_name}. Tried: "
            + "; ".join(errors)
        )
