from app.domains.products.intelligence.merge_candidate_models import MergeCandidateModel


def test_merge_candidate_model_table_name():
    assert MergeCandidateModel.__tablename__ == "merge_candidates"


def test_merge_candidate_model_has_required_columns():
    columns = MergeCandidateModel.__table__.columns

    assert "signature" in columns
    assert "master_title" in columns
    assert "offer_count" in columns
    assert "average_confidence" in columns
    assert "decision" in columns
    assert "status" in columns
    assert "offer_titles_json" in columns
    assert "sources_json" in columns
