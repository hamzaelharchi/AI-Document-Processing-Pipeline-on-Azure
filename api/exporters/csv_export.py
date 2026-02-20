import csv
import io
from models import ExtractionResult


class CsvExporter:
    def export(self, result: ExtractionResult) -> str:
        output = io.StringIO()

        if result.fields:
            writer = csv.writer(output)
            writer.writerow(["Field Name", "Value", "Confidence"])
            for field in result.fields:
                writer.writerow([field.name, field.value, f"{field.confidence:.2f}"])

            output.write("\n")

        if result.tables:
            for i, table in enumerate(result.tables):
                if i > 0:
                    output.write("\n")
                output.write(f"# Table {i + 1}\n")

                if isinstance(table, dict):
                    headers = table.get("headers", [])
                    rows = table.get("rows", [])

                    writer = csv.writer(output)
                    if headers:
                        writer.writerow(headers)
                    for row in rows:
                        writer.writerow(row)

                elif isinstance(table, list) and table:
                    writer = csv.writer(output)
                    for row in table:
                        if isinstance(row, list):
                            writer.writerow(row)

        return output.getvalue()
