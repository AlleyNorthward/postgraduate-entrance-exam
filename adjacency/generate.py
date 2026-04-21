import json
import os

PLACEHOLDER = "0000"

def load_config(path="config.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def build_filename(template: str, number: int):
    if PLACEHOLDER not in template:
        raise ValueError("filename_template must contain '0000' placeholder")

    num_str = f"{number:04d}"
    return template.replace(PLACEHOLDER, num_str)

def generate(config):
    start = config["start"]
    count = config["count"]
    output_dir = config.get("output_dir", ".")
    template = config["filename_template"]
    content = config["content"]
    overwrite = config.get("overwrite", False)

    os.makedirs(output_dir, exist_ok=True)

    for i in range(start, start + count):
        filename = build_filename(template, i)
        filepath = os.path.join(output_dir, filename)

        # 🛡️ 重复生成控制
        if os.path.exists(filepath) and not overwrite:
            print(f"Skip (exists): {filename}")
            continue

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        action = "Overwritten" if os.path.exists(filepath) and overwrite else "Created"
        print(f"{action}: {filename}")

if __name__ == "__main__":
    config = load_config("config.json")
    generate(config)
