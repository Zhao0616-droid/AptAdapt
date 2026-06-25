"""知识库初始化脚本

用法:
    python scripts/populate_kb.py --all          # 初始化所有课程
    python scripts/populate_kb.py computer_organization  # 初始化指定课程
    python scripts/populate_kb.py --list         # 列出可用课程
"""
import argparse
import sys
from pathlib import Path

# 把项目根目录加入 sys.path，方便直接运行
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.courses import COURSES
from app.services.retriever import populate_knowledge_base


def list_courses():
    print("可用课程:")
    for c in COURSES:
        print(f"  - {c['id']}: {c['name']}")


def main():
    parser = argparse.ArgumentParser(description="初始化 AptAdapt 向量知识库")
    parser.add_argument(
        "course",
        nargs="?",
        default="",
        help="课程 ID，例如 computer_organization",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="初始化所有课程",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="列出可用课程",
    )

    args = parser.parse_args()

    if args.list:
        list_courses()
        return

    if args.all:
        course_ids = [c["id"] for c in COURSES]
    elif args.course:
        course_ids = [args.course]
    else:
        print("请指定课程 ID，或使用 --all 初始化所有课程。")
        list_courses()
        sys.exit(1)

    # 校验课程 ID 是否有效
    valid_ids = {c["id"] for c in COURSES}
    invalid = set(course_ids) - valid_ids
    if invalid:
        print(f"未知课程 ID: {invalid}")
        list_courses()
        sys.exit(1)

    total = 0
    for cid in course_ids:
        print(f"\n=== 初始化课程: {cid} ===")
        try:
            n = populate_knowledge_base(cid)
            print(f"[{cid}] 成功入库 {n} 条知识片段")
            total += n
        except Exception as e:
            print(f"[{cid}] 初始化失败: {e}")
            raise

    print(f"\n=== 全部完成，共入库 {total} 条知识片段 ===")


if __name__ == "__main__":
    main()
