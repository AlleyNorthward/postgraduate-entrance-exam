import json
import os
from typing import List, Dict, Any

PLACEHOLDER = "0000"

def load_config(path="config.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_filename(template: str, number: int):
    if PLACEHOLDER not in template:
        raise ValueError("filename_template must contain '0000' placeholder")

    num_str = f"{number:04d}"
    return template.replace(PLACEHOLDER, num_str)


def build_table(columns: List[str], rows: int = 0) -> str:
    if not columns:
        raise ValueError("table columns cannot be empty")

    header = "|" + "|".join(columns) + "|"
    separator = "|" + "|".join([":---:" for _ in columns]) + "|"

    body_lines = []
    for _ in range(rows):
        body_lines.append("|" + "|".join(["" for _ in columns]) + "|")

    parts = [
        '<div align="center">',
        "",
        header,
        separator,
    ]

    if body_lines:
        parts.extend(body_lines)

    parts.extend([
        "",
        "</div>",
    ])

    return "\n".join(parts)


def build_block(block: Dict[str, Any]) -> str:
    block_type = block.get("type", "markdown")

    if block_type == "markdown":
        return block.get("text", "")

    if block_type == "table":
        title = block.get("title", "")
        columns = block.get("columns", ["id", "name", "relation", "target"])
        rows = block.get("rows", 0)
        table = build_table(columns=columns, rows=rows)

        if title:
            return f"{title}\n\n{table}"
        return table

    raise ValueError(f"Unknown block type: {block_type}")


def build_content(config: Dict[str, Any]) -> str:
    blocks = config.get("content_blocks")
    if not blocks:
        return config.get("content", "")

    content_parts = []
    for block in blocks:
        content_parts.append(build_block(block))

    return "\n" + "\n\n".join(content_parts).rstrip() + "\n"


def generate(config):
    start = config["start"]
    count = config["count"]
    output_dir = config.get("output_dir", ".")
    template = config["filename_template"]
    overwrite = config.get("overwrite", False)

    content = build_content(config)

    os.makedirs(output_dir, exist_ok=True)

    for i in range(start, start + count):
        filename = build_filename(template, i)
        filepath = os.path.join(output_dir, filename)

        existed_before = os.path.exists(filepath)

        if existed_before and not overwrite:
            print(f"Skip (exists): {filename}")
            continue

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        action = "Overwritten" if existed_before else "Created"
        print(f"{action}: {filename}")


if __name__ == "__main__":
    config = load_config("config.json")
    generate(config)
