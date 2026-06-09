import os
import json
from datetime import datetime

MEM_FILE = ".agent/memory/upload_history.json"
REWARD_DIR = ".agent/memory/reward"
PUNISH_DIR = ".agent/memory/punishment"

def auto_evaluate_performance():
    if not os.path.exists(MEM_FILE):
        return
    with open(MEM_FILE, "r") as f:
        history = json.load(f)

    for record in history:
        if record.get("status") == "published":
            meta = record.get("metadata", {})
            title = meta.get("youtube_title", "제목 없음")

            # [TODO: 실제 YouTube Analytics API를 호출해 views와 CTR을 수집하는 로직 대체]
            views = 15000  # 모의 값

            summary = {
                "Title": title,
                "Prompt Used": meta.get("veo_prompt"),
                "Views": views,
                "Feedback Date": datetime.now().strftime("%Y-%m-%d")
            }

            if views > 10000:
                with open(os.path.join(REWARD_DIR, "success_log.txt"), "a", encoding="utf-8") as f:
                    f.write(json.dumps(summary, ensure_ascii=False) + "\n")
            else:
                summary["Conclusion"] = "수익성(커머스) 결여 혹은 기괴한 연출로 이탈률 발생. 다음엔 실물 제품 타겟할 것."
                with open(os.path.join(PUNISH_DIR, "fail_log.txt"), "a", encoding="utf-8") as f:
                    f.write(json.dumps(summary, ensure_ascii=False) + "\n")

            record["status"] = "evaluated"  # 중복 판별 방지

    with open(MEM_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    auto_evaluate_performance()
