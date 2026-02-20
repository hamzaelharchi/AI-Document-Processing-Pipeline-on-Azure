from models import ExtractionResult


class MarkdownExporter:
    def export(self, result: ExtractionResult) -> str:
        lines = []

        lines.append(f"# Extracted Document: {result.document_id}")
        lines.append("")
        lines.append(f"**Processed:** {result.extracted_at.isoformat()}")
        lines.append(f"**Pages:** {result.page_count}")
        lines.append(f"**Confidence:** {result.confidence.overall:.1%}")
        if result.confidence.is_low_confidence:
            lines.append("⚠️ **Low confidence extraction - manual review recommended**")
        lines.append("")
        lines.append("---")
        lines.append("")

        if result.fields:
            lines.append("## Extracted Fields")
            lines.append("")
            for field in result.fields:
                confidence_indicator = "✓" if field.confidence >= 0.7 else "?"
                lines.append(f"- **{field.name}:** {field.value} {confidence_indicator}")
            lines.append("")
            lines.append("---")
            lines.append("")

        lines.append("## Document Content")
        lines.append("")
        lines.append(result.markdown_content)
        lines.append("")

        lines.append("---")
        lines.append(f"*Extracted by Mistral OCR ({result.model_version})*")

        return "\n".join(lines)
