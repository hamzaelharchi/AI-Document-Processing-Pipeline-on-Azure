import xml.etree.ElementTree as ET
from xml.dom import minidom
from models import ExtractionResult


class XmlExporter:
    def export(self, result: ExtractionResult) -> str:
        root = ET.Element("extraction")
        root.set("document_id", result.document_id)
        root.set("extracted_at", result.extracted_at.isoformat())
        root.set("model_version", result.model_version)

        metadata = ET.SubElement(root, "metadata")
        ET.SubElement(metadata, "page_count").text = str(result.page_count)
        ET.SubElement(metadata, "processing_time_ms").text = str(result.processing_time_ms)

        confidence_elem = ET.SubElement(metadata, "confidence")
        ET.SubElement(confidence_elem, "overall").text = f"{result.confidence.overall:.3f}"
        ET.SubElement(confidence_elem, "is_low_confidence").text = str(result.confidence.is_low_confidence).lower()

        if result.fields:
            fields_elem = ET.SubElement(root, "fields")
            for field in result.fields:
                field_elem = ET.SubElement(fields_elem, "field")
                field_elem.set("confidence", f"{field.confidence:.2f}")
                ET.SubElement(field_elem, "name").text = field.name
                ET.SubElement(field_elem, "value").text = str(field.value)

        if result.tables:
            tables_elem = ET.SubElement(root, "tables")
            for i, table in enumerate(result.tables):
                table_elem = ET.SubElement(tables_elem, "table")
                table_elem.set("index", str(i))

                if isinstance(table, dict):
                    headers = table.get("headers", [])
                    rows = table.get("rows", [])

                    if headers:
                        headers_elem = ET.SubElement(table_elem, "headers")
                        for h in headers:
                            ET.SubElement(headers_elem, "header").text = str(h)

                    rows_elem = ET.SubElement(table_elem, "rows")
                    for row in rows:
                        row_elem = ET.SubElement(rows_elem, "row")
                        for cell in row:
                            ET.SubElement(row_elem, "cell").text = str(cell)

        content = ET.SubElement(root, "content")
        raw_text = ET.SubElement(content, "raw_text")
        raw_text.text = result.raw_text

        rough_string = ET.tostring(root, encoding="unicode")
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")
