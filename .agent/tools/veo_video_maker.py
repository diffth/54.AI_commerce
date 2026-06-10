import os
import time
import io
from dotenv import load_dotenv

try:
    from google import genai
    from google.genai import types
    from PIL import Image
except ImportError:
    print("[ERROR] 패키지 없음: 'pip install google-genai pillow python-dotenv' 실행 요망")
    exit(1)

load_dotenv()
VEO_MODEL_ID = "veo-3.1-generate-preview"

_client = None

def get_client():
    """Gemini API 클라이언트를 필요한 시점에 싱글톤 패턴으로 안전하게 초기화합니다."""
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "[ERROR] GEMINI_API_KEY 환경 변수가 누락되었습니다.\n"
                "프로젝트 루트 디렉토리에 .env 파일을 생성하고 'GEMINI_API_KEY=your_key_here'를 설정해 주세요."
            )
        _client = genai.Client(api_key=api_key)
    return _client

def wait_for_active(vid_data, max_retries=120):
    """구글 클라우드 내부망에서 영상 후처리(ACTIVE)가 끝날 때까지 대기하여 연장 에러를 방지합니다."""
    client = get_client()
    # name 속성이 있다면 우선 사용하고, 없을 경우 uri를 파싱합니다.
    if hasattr(vid_data, 'name') and vid_data.name:
        file_name = vid_data.name
    elif hasattr(vid_data, 'uri') and vid_data.uri:
        file_name = f"files/{vid_data.uri.split('files/')[-1].split(':')[0]}"
    else:
        raise ValueError("비디오 데이터에 유효한 name 또는 uri 정보가 없습니다.")

    print(f"[WAIT] 후처리(ACTIVE) 상태 전환을 기다립니다: {file_name}")
    
    retries = 0
    while retries < max_retries:
        try:
            f = client.files.get(name=file_name)
            if hasattr(f, 'state') and "ACTIVE" in str(f.state).upper():
                print("[OK] 영상 활성화 완료. 다음 단계로 진입 가능합니다.")
                return f
        except Exception as e:
            print(f"[WARN] 파일 상태 조회 오류 (재시도 중): {e}")
        
        retries += 1
        time.sleep(5)
        
    raise TimeoutError(f"[TIMEOUT] 비디오가 {max_retries * 5}초 내에 ACTIVE 상태로 변환되지 않았습니다.")

def generate_long_take(image_path, base_prompt, extend_prompts=[], output_filename="result.mp4"):
    """
    이미지를 기반으로 첫 5초를 만들고, extend_prompts 배열 길이만큼 물고 늘어지며 영상을 롱테이크로 연장합니다.
    """
    client = get_client()
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"소스 이미지를 찾을 수 없습니다: {image_path}")

    img = Image.open(image_path).convert("RGB")
    b = io.BytesIO()
    img.save(b, format='JPEG')
    val_image = types.Image(image_bytes=b.getvalue(), mime_type="image/jpeg")

    print("\n[INFO] [1 Phase] 초기 5초 영상 렌더링 중...")
    op = client.models.generate_videos(
        model=VEO_MODEL_ID, prompt=base_prompt, image=val_image,
        config=types.GenerateVideosConfig(aspect_ratio="16:9", resolution="720p")
    )
    
    while not op.done:
        time.sleep(15)
        op = client.operations.get(operation=op)

    if not op.result or not op.result.generated_videos:
        raise RuntimeError("비디오 생성 초기 작업이 실패했거나 결과 비디오가 반환되지 않았습니다.")

    current_video = wait_for_active(op.result.generated_videos[0].video)

    # 전달받은 프롬프트 리스트만큼 무한 연장 (체이닝 로직)
    for idx, prompt in enumerate(extend_prompts):
        print(f"\n[INFO] [{idx+2} Phase] 비디오 연장(Extending) 중... (목표: +5초 추가)")
        ext_op = client.models.generate_videos(
            model=VEO_MODEL_ID, prompt=prompt, video=current_video, # File형 객체 직접 전달
            config=types.GenerateVideosConfig(number_of_videos=1, resolution="720p")
        )
        while not ext_op.done:
            time.sleep(15)
            ext_op = client.operations.get(operation=ext_op)
            
        if not ext_op.result or not ext_op.result.generated_videos:
            raise RuntimeError(f"비디오 연장 {idx+2} 단계가 실패했거나 결과가 존재하지 않습니다.")
            
        current_video = wait_for_active(ext_op.result.generated_videos[0].video)

    print("\n[OK] 모든 비디오 연장 시퀀스 완료! 다운로드 시작...")
    
    file_name_part = current_video.name if (hasattr(current_video, 'name') and current_video.name) else "files/" + current_video.uri.split("files/")[-1].split(":")[0]

    # name 대신 file 키워드 매개변수 사용 (최신 SDK 대응)
    video_bytes = client.files.download(file=file_name_part)
    with open(output_filename, 'wb') as f:
        f.write(video_bytes)
    print(f"[OK] 로컬 다운로드 성공: {output_filename}")

if __name__ == "__main__":
    # 테스트 구동
    extend_prompts = [
        "The scene smoothly transitions as the subject takes a bite.",
        "A beautiful close-up showing the detail of the food."
    ]
    # generate_long_take("sample.jpg", "Cinematic master shot...", extend_prompts, "my_ad.mp4")
