from app.domains.deal_notifications.provider_governance import NotificationExperimentService


def test_rc219_deterministic_variant_assignment():
    service = NotificationExperimentService()

    service.create_experiment(
        experiment_id="title-test",
        variants=["A","B"],
    )

    first = service.assign_variant(
        experiment_id="title-test",
        user_id="user-1",
    )
    second = service.assign_variant(
        experiment_id="title-test",
        user_id="user-1",
    )

    assert first["assigned"] is True
    assert first["variant"] == second["variant"]
