import json
import random
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union

ASSETS_DIR = Path("assets")
EXPORT_DIR = Path("export")

def ensure_question_stats(q: Dict[str, Any]) -> None:
    if "error_count" not in q:
        q["error_count"] = 0
    if "timeout_count" not in q:
        q["timeout_count"] = 0
    if "train_count" not in q:
        q["train_count"] = 0

def save_assets_questions(json_path: Path, questions: List[Dict[str, Any]]) -> None:
    try:
        with json_path.open("w", encoding="utf-8") as f:
            json.dump(questions, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"写回 assets 失败: {e}")

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

    ensure_question_stats(item)

    return {
        "id": item["id"],
        "question": item["question"],
        "answer": item["answer"],
        "error_count": item.get("error_count", 0),
        "timeout_count": item.get("timeout_count", 0),
        "train_count": item.get("train_count", 0),
    }

def get_reaction_time_limit_seconds() -> Optional[float]:
    while True:
        text = input("请输入反应限时(秒), 直接回车表示不启用: ").strip()
        if text == "":
            return None

        try:
            value = float(text)
            if value > 0:
                return value
        except ValueError:
            pass

        print("输入无效,请重新输入.")

def get_draw_count() -> int:
    while True:
        text = input("请输入每轮抽题数量, 默认10: ").strip()
        if text == "":
            return 10
        try:
            value = int(text)
            if value > 0:
                return value
        except ValueError:
            pass
        print("输入无效,请重新输入.")

def build_review_record(
    q: Dict[str, Any],
    user_answer: str,
    elapsed_seconds: float,
    reaction_time_limit_seconds: Optional[float],
) -> Dict[str, Any]:
    is_timeout = (
        reaction_time_limit_seconds is not None
        and elapsed_seconds > reaction_time_limit_seconds
    )

    return {
        "id": q["id"],
        "question": q["question"],
        "answer": q["answer"],
        "user_answer": user_answer,
        "elapsed_seconds": round(elapsed_seconds, 6),
        "reaction_time_limit_seconds": None if reaction_time_limit_seconds is None else round(reaction_time_limit_seconds, 6),
        "is_timeout": is_timeout,
    }

def sort_records_by_id(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    def sort_key(item: Dict[str, Any]):
        qid = item.get("id")
        try:
            return int(qid)
        except (TypeError, ValueError):
            return str(qid)

    return sorted(records, key=sort_key)

def export_review_records(
    export_path: Path,
    wrong_records: List[Dict[str, Any]],
    timeout_records: List[Dict[str, Any]],
) -> None:
    export_path.parent.mkdir(parents=True, exist_ok=True)

    export_data = {
        "wrong": sort_records_by_id(wrong_records),
        "time out": sort_records_by_id(timeout_records),
    }

    with export_path.open("w", encoding="utf-8") as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)

def format_multiline_text(value: Union[str, List[Any]]) -> str:
    if isinstance(value, list):
        return "\n".join(str(x) for x in value)
    return str(value)

def run_quiz_50_times(
    questions: List[Dict[str, Any]],
    reaction_time_limit_seconds: Optional[float],
    draw_count: int,
    raw_questions_ref: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:

    if not questions:
        print("题库为空,无法抽题.")
        return [], []

    original_pool = questions[:]
    current_pool = questions[:]
    wrong_records: List[Dict[str, Any]] = []
    timeout_records: List[Dict[str, Any]] = []
    recorded_ids = set()

    for round_idx in range(1,  draw_count+ 1):
        if not current_pool:
            current_pool = original_pool[:]
            print("\n当前轮题库已抽完,已重新载入题库继续抽题.")

        q = random.choice(current_pool)
        current_pool.remove(q)

        print("\n" + "=" * 60)
        print(f"第 {round_idx}/{draw_count} 次抽题")
        print(f"[题目 ID]: {q['id']}")
        print(f"[题目]: {format_multiline_text(q['question'])}")

        if reaction_time_limit_seconds is not None:
            print(f"[本题限时]: {reaction_time_limit_seconds:g} 秒")

        start_time = time.perf_counter()
        user_answer = input("请输入你的回答: ").strip()
        elapsed = time.perf_counter() - start_time

        print(f"[你的输入]: \n{user_answer}")
        print()
        print(f"[参考回答]: \n{format_multiline_text(q['answer'])}")
        print(f"[作答用时]: {elapsed:.3f} 秒")

        while True:
            judge = input("[判断结果]:回答正确 1,回答错误 0: ").strip()
            if judge in ("1", "0"):
                break
            print("输入无效,请重新输入 1 或 0.")

        is_timeout = (
            reaction_time_limit_seconds is not None
            and elapsed > reaction_time_limit_seconds
        )

        qid_text = str(q["id"])

        for rq in raw_questions_ref:
            if str(rq["id"]) == qid_text:
                rq["train_count"] += 1

                if judge == "0":
                    rq["error_count"] += 1

                if is_timeout:
                    rq["timeout_count"] += 1
                break

        if judge == "0":
            if qid_text not in recorded_ids:
                wrong_records.append(
                    build_review_record(
                        q=q,
                        user_answer=user_answer,
                        elapsed_seconds=elapsed,
                        reaction_time_limit_seconds=reaction_time_limit_seconds,
                    )
                )
                recorded_ids.add(qid_text)
            print("记录为: 错误题.\n")

        elif is_timeout:
            if qid_text not in recorded_ids:
                timeout_records.append(
                    build_review_record(
                        q=q,
                        user_answer=user_answer,
                        elapsed_seconds=elapsed,
                        reaction_time_limit_seconds=reaction_time_limit_seconds,
                    )
                )
                recorded_ids.add(qid_text)
            print("记录为: 超时但正确题.\n")

        else:
            print("回答正确.\n")

    return wrong_records, timeout_records

def process_single_json(json_path: Path, reaction_time_limit_seconds: Optional[float], draw_count: int) -> None:
    print(f"\n开始处理: {json_path}")

    raw_questions = load_questions_from_file(json_path)
    questions = [normalize_question(item) for item in raw_questions]

    wrong_records, timeout_records = run_quiz_50_times(
        questions,
        reaction_time_limit_seconds,
        draw_count,
        raw_questions
    )

    save_assets_questions(json_path, raw_questions)

    relative_path = json_path.relative_to(ASSETS_DIR)
    export_path = EXPORT_DIR / relative_path

    export_review_records(export_path, wrong_records, timeout_records)
    print(f"\n记录已导出到: {export_path}")

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

    reaction_time_limit_seconds = get_reaction_time_limit_seconds()
    draw_count = get_draw_count()

    while True:
        json_path = choose_json_file_step_by_step(ASSETS_DIR)
        if json_path is None:
            print("已退出.")
            break

        process_single_json(json_path, reaction_time_limit_seconds, draw_count)

        again = input("\n是否继续处理其他文件? 输入 1 继续, 其他任意键退出: ").strip()
        if again != "1":
            break

if __name__ == "__main__":
    main()
