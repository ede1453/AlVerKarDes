from app.domains.production_launch.service import ProductionLaunchService


def test_rc331_backup_register():
    s = ProductionLaunchService()
    assert s.register_backup(backup_id="b1",database_name="aici",size_bytes=100,checksum="abc")["registered"] is True
