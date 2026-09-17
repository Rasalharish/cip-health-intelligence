import pytest
import os
import sys

# Ensure model2 is in path
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)

from model2.deviation_engine import DeviationEngine

@pytest.fixture(scope="module")
def engine():
    return DeviationEngine()
