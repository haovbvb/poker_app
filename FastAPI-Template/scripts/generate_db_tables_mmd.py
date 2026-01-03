#!/usr/bin/env python3
"""Generate a Mermaid ER diagram for all DB tables.

Data source: Aerich/Tortoise migration SQL in `migrations/models/*.py`.

Outputs a Mermaid `.mmd` file (plain Mermaid text, no code fences).

Usage:
  python scripts/generate_db_tables_mmd.py
  python scripts/generate_db_tables_mmd.py --out 数据库表流程图.mmd
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS_DIR = WORKSPACE_ROOT / "migrations" / "models"
DEFAULT_OUT = WORKSPACE_ROOT / "数据库表流程图.mmd"


@dataclass(frozen=True)
class Column:
    name: str
    raw_type: str
    is_pk: bool
    is_fk: bool
    references_table: str | None
    references_column: str | None


@dataclass(frozen=True)
class Table:
    name: str
    columns: list[Column]


@dataclass(frozen=True)
class ForeignKey:
    from_table: str
    from_column: str
    to_table: str
    to_column: str


_RETURN_SQL_RE = re.compile(r"return\s+\"\"\"\s*(.*?)\"\"\"", re.DOTALL)

_CREATE_TABLE_PREFIX_RE = re.compile(
    r"CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+\"(?P<name>[^\"]+)\"\s*\(",
    re.IGNORECASE,
)

_COLUMN_LINE_RE = re.compile(r"^\s*\"(?P<name>[^\"]+)\"\s+(?P<rest>.+?)\s*,?\s*$")

_FK_RE = re.compile(
    r"REFERENCES\s+\"(?P<table>[^\"]+)\"\s*\(\s*\"(?P<column>[^\"]+)\"\s*\)",
    re.IGNORECASE,
)


def _iter_migration_files(migrations_dir: Path) -> Iterable[Path]:
    if not migrations_dir.exists():
        return []
    return sorted(p for p in migrations_dir.glob("*.py") if p.is_file())


def _extract_sql_blocks(py_text: str) -> list[str]:
    return [m.group(1) for m in _RETURN_SQL_RE.finditer(py_text)]


def _extract_tables(sql: str) -> list[tuple[str, str]]:
    """Extract CREATE TABLE bodies safely.

    We cannot use a simple regex for the body because column types like
    VARCHAR(255) contain parentheses.
    """

    results: list[tuple[str, str]] = []
    idx = 0
    while True:
        m = _CREATE_TABLE_PREFIX_RE.search(sql, idx)
        if not m:
            break

        table_name = m.group("name")
        # m ends right after the opening parenthesis "("
        body_start = m.end()

        depth = 1
        i = body_start
        while i < len(sql) and depth > 0:
            ch = sql[i]
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
            i += 1

        if depth != 0:
            # Unbalanced; stop to avoid infinite loop
            break

        body_end = i - 1  # position of the matching ')'
        body = sql[body_start:body_end]
        results.append((table_name, body))

        idx = i

    return results


def _sql_type_to_mermaid(raw_type: str) -> str:
    t = raw_type.strip().upper()
    if t.startswith("VARCHAR"):
        return "varchar"
    if t.startswith("INTEGER") or t == "INT":
        return "int"
    if t.startswith("BIGINT"):
        return "bigint"
    if t.startswith("TIMESTAMP"):
        return "datetime"
    if t.startswith("TEXT"):
        return "text"
    if t.startswith("JSON"):
        return "json"
    return t.lower().split()[0]


def _sanitize_entity_name(table_name: str) -> str:
    name = re.sub(r"[^0-9a-zA-Z_]", "_", table_name)
    name = re.sub(r"_+", "_", name).strip("_")
    name = name.upper() if name else "TABLE"
    if name[0].isdigit():
        name = f"T_{name}"
    return name


def parse_migrations(migrations_dir: Path) -> tuple[dict[str, Table], list[ForeignKey]]:
    tables: dict[str, Table] = {}
    fks: list[ForeignKey] = []

    for path in _iter_migration_files(migrations_dir):
        text = path.read_text(encoding="utf-8")
        for sql in _extract_sql_blocks(text):
            for table_name, body in _extract_tables(sql):
                columns: list[Column] = []
                for line in body.splitlines():
                    stripped = line.strip()
                    if not stripped:
                        continue
                    # Skip table-level constraints
                    if stripped.upper().startswith("CONSTRAINT "):
                        continue

                    m = _COLUMN_LINE_RE.match(line)
                    if not m:
                        continue

                    col_name = m.group("name")
                    rest = m.group("rest")

                    # Infer raw type as the first token (or VARCHAR(...))
                    raw_type = rest.split()[0]
                    if raw_type.upper().startswith("VARCHAR"):
                        # keep full VARCHAR(123)
                        raw_type = raw_type

                    is_pk = "PRIMARY KEY" in rest.upper()
                    fk_match = _FK_RE.search(rest)
                    is_fk = fk_match is not None
                    ref_table = fk_match.group("table") if fk_match else None
                    ref_col = fk_match.group("column") if fk_match else None

                    columns.append(
                        Column(
                            name=col_name,
                            raw_type=raw_type,
                            is_pk=is_pk,
                            is_fk=is_fk,
                            references_table=ref_table,
                            references_column=ref_col,
                        )
                    )

                    if fk_match:
                        fks.append(
                            ForeignKey(
                                from_table=table_name,
                                from_column=col_name,
                                to_table=ref_table or "",
                                to_column=ref_col or "",
                            )
                        )

                # If a table appears across multiple migrations, keep the latest definition.
                tables[table_name] = Table(name=table_name, columns=columns)

    return tables, fks


def render_mermaid(tables: dict[str, Table], fks: list[ForeignKey]) -> str:
    # Stable ordering for readability
    table_names = sorted(tables.keys())
    entity_map = {t: _sanitize_entity_name(t) for t in table_names}

    lines: list[str] = []
    lines.append("%% Auto-generated from migrations/models/*.py")
    lines.append("%% Regenerate: python scripts/generate_db_tables_mmd.py")
    lines.append("erDiagram")

    for table_name in table_names:
        table = tables[table_name]
        entity = entity_map[table_name]
        lines.append(f"    %% table: {table_name}")
        lines.append(f"    {entity} {{")
        for col in table.columns:
            t = _sql_type_to_mermaid(col.raw_type)
            flags = []
            if col.is_pk:
                flags.append("PK")
            if col.is_fk:
                flags.append("FK")
            flag_str = (" " + " ".join(flags)) if flags else ""
            lines.append(f"        {t} {col.name}{flag_str}")
        lines.append("    }")
        lines.append("")

    # Deduplicate FK relationships
    seen: set[tuple[str, str, str, str]] = set()
    for fk in fks:
        key = (fk.from_table, fk.from_column, fk.to_table, fk.to_column)
        if key in seen:
            continue
        seen.add(key)

        if fk.from_table not in entity_map or fk.to_table not in entity_map:
            continue

        child = entity_map[fk.from_table]
        parent = entity_map[fk.to_table]
        # parent(1) -> child(many)
        lines.append(f"    {parent} ||--o{{ {child} : {fk.from_column}")

    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate Mermaid ER diagram for DB tables."
    )
    parser.add_argument(
        "--migrations", default=str(MIGRATIONS_DIR), help="Path to migrations/models"
    )
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="Output .mmd path")
    args = parser.parse_args()

    migrations_dir = Path(args.migrations)
    out_path = Path(args.out)

    tables, fks = parse_migrations(migrations_dir)
    if not tables:
        raise SystemExit(f"No tables found under: {migrations_dir}")

    mermaid = render_mermaid(tables, fks)
    out_path.write_text(mermaid, encoding="utf-8")
    print(f"Wrote: {out_path} (tables={len(tables)}, fks={len(fks)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
