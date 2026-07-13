from app.domains.production_launch.service import ProductionLaunchService


def test_rc332_backup_verify():
    s = ProductionLaunchService()
    s.register_backup(backup_id="b1",database_name="aici",size_bytes=100,checksum="abc")
    assert s.verify_backup(backup_id="b1",observed_checksum="abc")["verified"] is True