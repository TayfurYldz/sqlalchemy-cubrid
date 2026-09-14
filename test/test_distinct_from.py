from __future__ import annotations

import os

import pytest
import sqlalchemy as sa
from sqlalchemy import create_engine, select

_DEFAULT_URL = "cubrid://dba@localhost:33000/testdb"


def _cubrid_url() -> str:
    return os.environ.get("CUBRID_TEST_URL", _DEFAULT_URL)


def _can_connect() -> bool:
    try:
        engine = create_engine(_cubrid_url())
        with engine.connect() as conn:
            conn.execute(sa.text("SELECT 1"))
        engine.dispose()
        return True
    except Exception:
        return False


_available = _can_connect()
pytestmark = pytest.mark.skipif(
    not _available,
    reason="CUBRID instance not available (set CUBRID_TEST_URL)",
)


@pytest.fixture(scope="module")
def engine():
    eng = create_engine(_cubrid_url(), echo=False)
    yield eng
    eng.dispose()


@pytest.mark.parametrize(
    ("left", "right", "expected_distinct", "expected_not_distinct"),
    [
        (1, 1, False, True),
        (1, 2, True, False),
        (None, None, False, True),
        (None, 1, True, False),
    ],
)
def test_is_distinct_from_truth_table(
    engine, left, right, expected_distinct, expected_not_distinct
):
    left_value = sa.literal(left)
    right_value = sa.literal(right)

    stmt = select(
        left_value.is_distinct_from(right_value).label("is_distinct"),
        left_value.is_not_distinct_from(right_value).label("is_not_distinct"),
    )

    with engine.connect() as conn:
        row = conn.execute(stmt).one()

    assert bool(row.is_distinct) is expected_distinct
    assert bool(row.is_not_distinct) is expected_not_distinct
