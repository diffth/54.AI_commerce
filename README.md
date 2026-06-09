# 54.AI_commerce

100% 자율주행 풀 오토메이션 에이전트 **영식(Young-sik)**을 활용한 YouTube 커머스 자동화 프로젝트입니다.

## 주요 기능 및 구성 요소
- **에이전트 스킬 설정 (`.agent/skills/agent-youngsik/SKILL.md`)**: 영식의 페르소나 및 핵심 미션 설정
- **비디오 제작 엔진 (`.agent/tools/veo_video_maker.py`)**: Google Veo 3.1 API를 활용한 고화질 롱테이크 비디오 자동 생성
- **성과 자율 평가 (`.agent/tools/evaluate_feedback.py`)**: 강화학습(RL) 기반 성과 분석 및 피드백 오답 노트 생성

## 디렉토리 구조
```
.agent/
├── memory/
│   ├── punishment/     # 이탈률이 높은 실패 영상 피드백 보관
│   └── reward/         # 성공한 영상 로그 보관
├── skills/
│   └── agent-youngsik/
│       └── SKILL.md    # 에이전트 정의 및 규칙
└── tools/
    ├── evaluate_feedback.py  # 성과 평가 및 오답 노트 작성
    └── veo_video_maker.py    # Veo 3.1 비디오 생성 및 연장 엔진
output_assets/                # 생성된 비디오 에셋 저장 공간
```
