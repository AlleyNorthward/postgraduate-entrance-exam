import json
import random
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union


ASSETS_DIR = Path("assets")
EXPORT_DIR = Path("export")
DRAW_COUNT = 50


def load_questions_from_file(json_path: Path) -> List[Dict[str, Any]]:
    with json_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        for key in ("questions", "items", "data"):
            if key in data and isinstance(data[key], list):
                return data[key]

    raise ValueError(f"{json_path} 的 JSON 格式不符合要求.")


def normalize_question(item: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(item, dict):
        raise ValueError("题目项必须是字典.")

    if "id" not in item:
        raise ValueError(f"题目缺少 id 字段: {item}")
    if "question" not in item:
        raise ValueError(f"题目缺少 question 字段: {item}")
    if "answer" not in item:
        raise ValueError(f"题目缺少 answer 字段: {item}")

    return {
        "id": item["id"],
        "question": item["question"],
        "answer": item["answer"]
    }

def export_wrong_questions(export_path: Path, wrong_questions: List[Dict[str, Any]]) -> None:
    export_path.parent.mkdir(parents=True, exist_ok=True)

    unique_map = {}
    for q in wrong_questions:
        unique_map[str(q["id"])] = {
            "id": q["id"],
            "question": q["question"],
            "answer": q["answer"]
        }

    def sort_key(item: Dict[str, Any]):
        qid = item.get("id")
        try:
            return int(qid)
        except (TypeError, ValueError):
            return str(qid)

    sorted_questions = sorted(unique_map.values(), key=sort_key)

    with export_path.open("w", encoding="utf-8") as f:
        json.dump(sorted_questions, f, ensure_ascii=False, indent=2)


def format_multiline_text(value: Union[str, List[Any]]) -> str:
    if isinstance(value, list):
        return "\n".join(str(x) for x in value)
    return str(value)


def run_quiz_50_times(questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not questions:
        print("题库为空,无法抽题.")
        return []

    original_pool = questions[:]
    current_pool = questions[:]
    wrong_questions = []

    for round_idx in range(1, DRAW_COUNT + 1):
        if not current_pool:
            current_pool = original_pool[:]
            print("\n当前轮题库已抽完,已重新载入题库继续抽题.")

        q = random.choice(current_pool)
        current_pool.remove(q)

        print("\n" + "=" * 60)
        print(f"第 {round_idx}/{DRAW_COUNT} 次抽题")
        print(f"题目 ID: {q['id']}")
        print(f"题目: {format_multiline_text(q['question'])}")

        user_answer = input("请输入你的回答: ").strip()
        print(f"你的输入: {user_answer}")
        print(f"参考回答: {format_multiline_text(q['answer'])}")

        while True:
            judge = input("判断结果:回答正确 1,回答错误 0: ").strip()
            if judge in ("1", "0"):
                break
            print("输入无效,请重新输入 1 或 0.")

        if judge == "0":
            wrong_questions.append(q)

    return wrong_questions


def process_single_json(json_path: Path) -> None:
    print(f"\n开始处理: {json_path}")

    raw_questions = load_questions_from_file(json_path)
    questions = [normalize_question(item) for item in raw_questions]

    wrong_questions = run_quiz_50_times(questions)

    relative_path = json_path.relative_to(ASSETS_DIR)
    export_path = EXPORT_DIR / relative_path

    export_wrong_questions(export_path, wrong_questions)
    print(f"\n错题已导出到: {export_path}")


def list_directory_entries(current_dir: Path) -> Tuple[List[Path], List[Path]]:
    dirs = sorted([p for p in current_dir.iterdir() if p.is_dir()], key=lambda x: x.name.lower())
    files = sorted(
        [p for p in current_dir.iterdir() if p.is_file() and p.suffix.lower() == ".json"],
        key=lambda x: x.name.lower()
    )
    return dirs, files


def choose_json_file_step_by_step(root_dir: Path) -> Optional[Path]:
    current_dir = root_dir

    while True:
        dirs, files = list_directory_entries(current_dir)

        print("\n" + "=" * 60)
        print(f"当前目录: {current_dir}")

        if current_dir == root_dir:
            print("0. 退出")
        else:
            print("0. 返回上一级")

        mapping = {}
        idx = 1

        for d in dirs:
            print(f"{idx}. [文件夹] {d.name}")
            mapping[str(idx)] = ("dir", d)
            idx += 1

        for f in files:
            print(f"{idx}. [文件] {f.name}")
            mapping[str(idx)] = ("file", f)
            idx += 1

        if not dirs and not files:
            print("当前目录下没有内容.")
            choice = input("输入 0 返回上一级: ").strip()
            if choice == "0":
                if current_dir == root_dir:
                    return None
                current_dir = current_dir.parent
            else:
                print("输入无效,请重新输入.")
            continue

        choice = input("\n请选择: ").strip()

        if choice == "0":
            if current_dir == root_dir:
                return None
            current_dir = current_dir.parent
            continue

        if choice not in mapping:
            print("输入无效,请重新输入.")
            continue

        kind, path = mapping[choice]

        if kind == "file":
            return path

        current_dir = path


def main():
    if not ASSETS_DIR.exists():
        print(f"找不到目录: {ASSETS_DIR.resolve()}")
        return

    while True:
        json_path = choose_json_file_step_by_step(ASSETS_DIR)
        if json_path is None:
            print("已退出.")
            break

        process_single_json(json_path)

        again = input("\n是否继续处理其他文件? 输入 1 继续, 其他任意键退出: ").strip()
        if again != "1":
            break


if __name__ == "__main__":
    main()
