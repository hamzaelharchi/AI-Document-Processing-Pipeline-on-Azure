import pytest
import sys
from pathlib import Path

# Add api/ directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "api"))

from models import ExtractionConfidence


class TestExtractionConfidence:
    def test_calculate_high_confidence(self):
        confidences = [0.95, 0.92, 0.88, 0.90]
        result = ExtractionConfidence.calculate(confidences)

        assert result.overall == pytest.approx(0.9125, rel=0.01)
        assert result.is_low_confidence is False

    def test_calculate_low_confidence(self):
        confidences = [0.5, 0.6, 0.55]
        result = ExtractionConfidence.calculate(confidences)

        assert result.overall < 0.7
        assert result.is_low_confidence is True

    def test_calculate_empty_list(self):
        result = ExtractionConfidence.calculate([])

        assert result.overall == 0.0
        assert result.is_low_confidence is True

    def test_calculate_single_value(self):
        result = ExtractionConfidence.calculate([0.85])

        assert result.overall == pytest.approx(0.85)
        assert result.is_low_confidence is False

    def test_calculate_custom_threshold(self):
        confidences = [0.75, 0.78]
        result = ExtractionConfidence.calculate(confidences, threshold=0.8)

        assert result.is_low_confidence is True

    def test_calculate_boundary_case(self):
        confidences = [0.7]
        result = ExtractionConfidence.calculate(confidences, threshold=0.7)

        assert result.is_low_confidence is False
