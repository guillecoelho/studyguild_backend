import os
from pathlib import Path

import yaml
from django.core.management.base import BaseCommand, CommandError

from apps.academics.models import Subject, SubjectGroup
from apps.institutions.models import Institution


class Command(BaseCommand):
    help = "Import scraped subjects from db/data into an institution (default id=1)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--institution-id",
            type=int,
            default=int(os.environ.get("INSTITUTION_ID", "1")),
        )
        parser.add_argument(
            "--data-dir",
            type=Path,
            default=None,
            help="Root dir to search for scraped_subjects.yml (default: ./data)",
        )

    def handle(self, *args, **options):
        institution_id = options["institution_id"]
        try:
            institution = Institution.objects.get(pk=institution_id)
        except Institution.DoesNotExist:
            raise CommandError(f"Institution with id={institution_id} was not found.")

        data_dir = options["data_dir"]
        if data_dir is None:
            data_dir = Path(__file__).resolve().parents[4] / "data"

        scraped_files = sorted(data_dir.rglob("scraped_subjects.yml"))
        if not scraped_files:
            self.stdout.write(f"No scraped_subjects.yml files found under {data_dir}.")
            return

        stats = {
            "files": len(scraped_files),
            "rows_seen": 0,
            "created": 0,
            "updated": 0,
            "unchanged": 0,
            "skipped_blank": 0,
            "groups_created": 0,
            "groups_attached": 0,
            "groups_missing_definition": 0,
        }

        for subjects_file in scraped_files:
            parent = subjects_file.parent
            subjects_data = self._load_yaml(subjects_file)
            overrides_data = self._load_yaml(parent / "subject_overrides.yml")
            groups_data = self._load_yaml(parent / "scraped_subject_groups.yml")

            groups_by_code = {}
            for group_code, group_payload in groups_data.items():
                group_payload = group_payload if isinstance(group_payload, dict) else {}
                group_name = (group_payload.get("name") or "").strip()
                group_code_str = (group_payload.get("code") or group_code or "").strip()

                if not group_name and not group_code_str:
                    continue

                resolved_name = group_name or group_code_str
                subject_group, created = SubjectGroup.objects.get_or_create(
                    institution=institution,
                    name=resolved_name,
                )
                if created:
                    stats["groups_created"] += 1

                groups_by_code[group_code_str] = subject_group
                groups_by_code[str(group_code)] = subject_group

            for raw_code, payload in subjects_data.items():
                stats["rows_seen"] += 1

                payload = payload if isinstance(payload, dict) else {}
                code = (payload.get("code") or raw_code or "").strip()
                name = (payload.get("name") or "").strip()

                if not code or not name:
                    stats["skipped_blank"] += 1
                    continue

                overrides = overrides_data.get(code) or overrides_data.get(str(raw_code)) or {}
                short_name = (overrides.get("short_name") or "").strip() or None

                subject, created = Subject.objects.get_or_create(
                    institution=institution,
                    code=code,
                    defaults={"name": name, "abreviated_name": short_name},
                )

                if created:
                    stats["created"] += 1
                else:
                    changed = False
                    if subject.name != name:
                        subject.name = name
                        changed = True
                    if subject.abreviated_name != short_name:
                        subject.abreviated_name = short_name
                        changed = True
                    if changed:
                        subject.save()
                        stats["updated"] += 1
                    else:
                        stats["unchanged"] += 1

                raw_groups = payload.get("subject_groups")
                group_codes = []
                if isinstance(raw_groups, list):
                    for entry in raw_groups:
                        if isinstance(entry, dict):
                            gc = (entry.get("group") or "").strip()
                            if gc:
                                group_codes.append(gc)

                existing_group_ids = set(subject.subject_groups.values_list("id", flat=True))
                for gc in group_codes:
                    subject_group = groups_by_code.get(gc)
                    if subject_group is None:
                        stats["groups_missing_definition"] += 1
                        subject_group, _ = SubjectGroup.objects.get_or_create(
                            institution=institution,
                            name=gc,
                        )
                        groups_by_code[gc] = subject_group

                    if subject_group.id not in existing_group_ids:
                        subject.subject_groups.add(subject_group)
                        existing_group_ids.add(subject_group.id)
                        stats["groups_attached"] += 1

        self.stdout.write(
            f"Imported scraped subjects for institution {institution.id} ({institution.name})."
        )
        self.stdout.write(
            f"files={stats['files']} rows_seen={stats['rows_seen']} "
            f"created={stats['created']} updated={stats['updated']} "
            f"unchanged={stats['unchanged']} skipped_blank={stats['skipped_blank']}"
        )
        self.stdout.write(
            f"groups_created={stats['groups_created']} "
            f"groups_attached={stats['groups_attached']} "
            f"groups_missing_definition={stats['groups_missing_definition']}"
        )

    def _load_yaml(self, path: Path) -> dict:
        if path.exists():
            with open(path) as f:
                return yaml.safe_load(f) or {}
        return {}
