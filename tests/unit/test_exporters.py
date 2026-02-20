import pytest
import json
from datetime import datetime
import sys
from pathlib import Path

# Add api/ directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "api"))

from models import ExtractionResult, ExtractionConfidence, ExtractedField
from exporters import MarkdownExporter, JsonExporter, CsvExporter, XmlExporter


@pytest.fixture
def sample_result():
    return ExtractionResult(
        document_id="test_invoice",
        raw_text="Invoice content here",
        markdown_content="# Invoice\n\n**Vendor:** Test Corp\n**Amount:** $100",
        fields=[
            ExtractedField(name="Vendor", value="Test Corp", confidence=0.95),
            ExtractedField(name="Amount", value="$100", confidence=0.88),
        ],
        tables=[
            {"headers": ["Item", "Price"], "rows": [["Widget", "$50"], ["Gadget", "$50"]]}
        ],
        confidence=ExtractionConfidence(overall=0.91, is_low_confidence=False),
        page_count=1,
        processing_time_ms=1500,
        extracted_at=datetime(2024, 1, 15, 10, 30, 0),
        model_version="mistral-ocr-2503"
    )


class TestMarkdownExporter:
    def test_export_includes_header(self, sample_result):
        exporter = MarkdownExporter()
        output = exporter.export(sample_result)

        assert "# Extracted Document: test_invoice" in output
        assert "**Confidence:** 91.0%" in output

    def test_export_includes_fields(self, sample_result):
        exporter = MarkdownExporter()
        output = exporter.export(sample_result)

        assert "## Extracted Fields" in output
        assert "**Vendor:** Test Corp" in output
        assert "**Amount:** $100" in output

    def test_export_includes_content(self, sample_result):
        exporter = MarkdownExporter()
        output = exporter.export(sample_result)

        assert "## Document Content" in output
        assert "# Invoice" in output

    def test_export_includes_model_version(self, sample_result):
        exporter = MarkdownExporter()
        output = exporter.export(sample_result)

        assert "mistral-ocr-2503" in output


class TestJsonExporter:
    def test_export_valid_json(self, sample_result):
        exporter = JsonExporter()
        output = exporter.export(sample_result)

        data = json.loads(output)
        assert data["document_id"] == "test_invoice"

    def test_export_includes_all_fields(self, sample_result):
        exporter = JsonExporter()
        output = exporter.export(sample_result)

        data = json.loads(output)
        assert "confidence" in data
        assert "fields" in data
        assert "tables" in data
        assert "content" in data

    def test_export_confidence_structure(self, sample_result):
        exporter = JsonExporter()
        output = exporter.export(sample_result)

        data = json.loads(output)
        assert data["confidence"]["overall"] == pytest.approx(0.91)
        assert data["confidence"]["is_low_confidence"] is False


class TestCsvExporter:
    def test_export_includes_fields(self, sample_result):
        exporter = CsvExporter()
        output = exporter.export(sample_result)

        assert "Field Name,Value,Confidence" in output
        assert "Vendor,Test Corp" in output

    def test_export_includes_tables(self, sample_result):
        exporter = CsvExporter()
        output = exporter.export(sample_result)

        assert "# Table 1" in output
        assert "Widget" in output
        assert "Gadget" in output


class TestXmlExporter:
    def test_export_valid_xml(self, sample_result):
        exporter = XmlExporter()
        output = exporter.export(sample_result)

        assert '<?xml version="1.0" ?>' in output
        assert "<extraction" in output
        assert "</extraction>" in output

    def test_export_includes_document_id(self, sample_result):
        exporter = XmlExporter()
        output = exporter.export(sample_result)

        assert 'document_id="test_invoice"' in output

    def test_export_includes_fields(self, sample_result):
        exporter = XmlExporter()
        output = exporter.export(sample_result)

        assert "<fields>" in output
        assert "<name>Vendor</name>" in output
        assert "<value>Test Corp</value>" in output
