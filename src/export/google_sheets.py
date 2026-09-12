import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from src.config.settings import settings
from src.database.repository import Repository
from src.utils.logging import logger

TAB_CONFIG = [
    {"table": "startups", "sheet_title": "Startups"},
    {"table": "products", "sheet_title": "Products"},
    {"table": "research_papers", "sheet_title": "Research Papers"},
    {"table": "jobs", "sheet_title": "Jobs"},
    {"table": "news", "sheet_title": "News"},
    {"table": "entity_mappings", "sheet_title": "Entity Mapping Log"}
]

class Exporter:
    """Exports pipeline database records to Google Sheets (6 tabs) or local CSV mirror."""

    @staticmethod
    def export_to_csv(output_dir: Optional[Path] = None) -> Dict[str, str]:
        """Exports all 6 tabs to CSV files in the data directory."""
        target_dir = output_dir or (settings.DATA_DIR / "sheets_export")
        target_dir.mkdir(parents=True, exist_ok=True)
        results: Dict[str, str] = {}

        for cfg in TAB_CONFIG:
            table = cfg["table"]
            title = cfg["sheet_title"]
            csv_path = target_dir / f"{title.replace(' ', '_').lower()}.csv"

            rows = Repository.get_all_rows(table)
            if not rows:
                logger.info(f"[CSV Exporter] Table '{table}' has 0 rows.")
                # Write empty CSV with headers if defined
                continue

            fieldnames = list(rows[0].keys())
            with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)

            logger.info(f"[CSV Exporter] Exported {len(rows)} rows to {csv_path.name}")
            results[title] = str(csv_path)

        return results

    @staticmethod
    def export_to_google_sheets(
        spreadsheet_id: Optional[str] = settings.GOOGLE_SHEET_ID,
        service_account_json: Optional[str] = settings.GOOGLE_SERVICE_ACCOUNT_JSON
    ) -> bool:
        """Exports all 6 tabs to Google Sheets using gspread batch updates."""
        if not spreadsheet_id or not service_account_json:
            logger.info("[Google Sheets Exporter] Credentials not supplied. Falling back to local CSV export.")
            Exporter.export_to_csv()
            return False

        try:
            import gspread
            from google.oauth2.service_account import Credentials

            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]

            # Check if service_account_json is a file path or raw JSON string
            if Path(service_account_json).is_file():
                creds = Credentials.from_service_account_file(service_account_json, scopes=scopes)
            else:
                creds_dict = json.loads(service_account_json)
                creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)

            client = gspread.authorize(creds)
            sheet = client.open_by_key(spreadsheet_id)

            for cfg in TAB_CONFIG:
                table = cfg["table"]
                title = cfg["sheet_title"]
                rows = Repository.get_all_rows(table)
                if not rows:
                    continue

                # Ensure worksheet exists
                try:
                    worksheet = sheet.worksheet(title)
                except gspread.WorksheetNotFound:
                    worksheet = sheet.add_worksheet(title=title, rows=len(rows) + 50, cols=len(rows[0]) + 5)

                worksheet.clear()
                headers = list(rows[0].keys())
                matrix = [headers]
                for r in rows:
                    matrix.append([str(r[h]) if r[h] is not None else "" for h in headers])

                # Batch write to avoid quota limits
                worksheet.update("A1", matrix)
                logger.info(f"[Google Sheets] Updated tab '{title}' with {len(rows)} rows.")

            return True

        except Exception as e:
            logger.error(f"[Google Sheets Exporter] Error uploading to Google Sheets: {e}. Falling back to CSV export.")
            Exporter.export_to_csv()
            return False
