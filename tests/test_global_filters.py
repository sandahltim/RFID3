import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.db_models import ItemMaster
from app.utils.filters import build_global_filters, apply_global_filters


def test_build_global_filters_conditions():
    filters = build_global_filters("3607", "rental")
    assert len(filters) == 2


def test_apply_global_filters_query_compilation():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    session = Session()
    query = session.query(ItemMaster)
    query = apply_global_filters(query, "3607", "rental")
    compiled = str(query.statement.compile(compile_kwargs={"literal_binds": True}))
    assert "home_store = '3607'" in compiled
    assert "identifier_type = 'rental'" in compiled
