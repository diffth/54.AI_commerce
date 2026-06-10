import os
import json
from datetime import datetime

MEM_FILE = ".agent/memory/upload_history.json"
REWARD_DIR = ".agent/memory/reward"
PUNISH_DIR = ".agent/memory/punishment"

def auto_evaluate_performance():
    # 폴더가 없으면 에러가 날 수 있으므로 자동 생성해 줍니다.
    os.makedirs(REWARD_DIR, exist_ok=True)
    os.makedirs(PUNISH_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(MEM_FILE), exist_ok=True)

    if not os.path.exists(MEM_FILE):
        # 파일이 없을 경우 빈 리스트로 초기화하여 새로 생성해 줍니다.
        with open(MEM_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, indent=4, ensure_ascii=False)
        return

    try:
        with open(MEM_FILE, "r", encoding="utf-8") as f:
            history = json.load(f)
        if not isinstance(history, list):
            print("[WARN] upload_history.json의 데이터 포맷이 올바르지 않습니다. 빈 리스트로 초기화합니다.")
            history = []
    except (json.JSONDecodeError, FileNotFoundError, PermissionError) as e:
        print(f"[WARN] upload_history.json 읽기/파싱 실패 ({e}). 새로운 기록 리스트를 시작합니다.")
        history = []

    has_changes = False
    for record in history:
        if not isinstance(record, dict):
            continue
            
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

            try:
                if views > 10000:
                    with open(os.path.join(REWARD_DIR, "success_log.txt"), "a", encoding="utf-8") as f:
                        f.write(json.dumps(summary, ensure_ascii=False) + "\n")
                else:
                    summary["Conclusion"] = "수익성(커머스) 결여 혹은 기괴한 연출로 이탈률 발생. 다음엔 실물 제품 타겟할 것."
                    with open(os.path.join(PUNISH_DIR, "fail_log.txt"), "a", encoding="utf-8") as f:
                        f.write(json.dumps(summary, ensure_ascii=False) + "\n")
                
                record["status"] = "evaluated"  # 중복 판별 방지
                has_changes = True
            except Exception as e:
                print(f"[ERROR] 피드백 로그 작성 실패: {e}")

    if has_changes:
        try:
            with open(MEM_FILE, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=4, ensure_ascii=False)
            print("[OK] 피드백 평가 및 결과 반영을 성공적으로 마쳤습니다.")
        except Exception as e:
            print(f"[ERROR] {MEM_FILE} 업데이트 실패: {e}")

if __name__ == "__main__":
    auto_evaluate_performance()
