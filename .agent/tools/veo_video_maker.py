import os
import time
import io
from dotenv import load_dotenv

try:
    from google import genai
    from google.genai import types
    from PIL import Image
except ImportError:
    print("❌ 패키지 없음: 'pip install google-genai pillow python-dotenv' 실행 요망")
    exit(1)

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
VEO_MODEL_ID = "veo-3.1-generate-preview"

def wait_for_active(vid_data):
    """구글 클라우드 내부망에서 영상 후처리(ACTIVE)가 끝날 때까지 대기하여 연장 에러를 방지합니다."""
    file_name = f"files/{vid_data.uri.split('files/')[-1].split(':')[0]}"
    print(f"⏳ [서버 대기] 후처리(ACTIVE) 상태 전환을 기다립니다: {file_name}")
    while True:
        try:
            f = client.files.get(name=file_name)
            if hasattr(f, 'state') and "ACTIVE" in str(f.state).upper():
                print("✅ [완료] 영상 활성화 완료. 다음 노드로 진입 가능합니다.")
                break
        except Exception:
            pass
        time.sleep(5)
    return vid_data

def generate_long_take(image_path, base_prompt, extend_prompts=[], output_filename="result.mp4"):
    """
    이미지를 기반으로 첫 5초를 만들고, extend_prompts 배열 길이만큼 물고 늘어지며 영상을 롱테이크로 연장합니다.
    """
    img = Image.open(image_path).convert("RGB")
    b = io.BytesIO()
    img.save(b, format='JPEG')
    val_image = types.Image(image_bytes=b.getvalue(), mime_type="image/jpeg")

    print("\n🎬 [1 Phase] 초기 5초 영상 렌더링 중...")
    op = client.models.generate_videos(
        model=VEO_MODEL_ID, prompt=base_prompt, image=val_image,
        config=types.GenerateVideosConfig(aspect_ratio="16:9", resolution="720p")
    )
    while not op.done:
        time.sleep(15)
        op = client.operations.get(operation=op)

    current_video = wait_for_active(op.result.generated_videos[0].video)

    # 전달받은 프롬프트 리스트만큼 무한 연장 (체이닝 로직)
    for idx, prompt in enumerate(extend_prompts):
        print(f"\n🎬 [{idx+2} Phase] 비디오 연장(Extending) 중... (목표: +5초 추가)")
        ext_op = client.models.generate_videos(
            model=VEO_MODEL_ID, prompt=prompt, video=current_video, # File형 포장이 아닌 객체 직접 전달
            config=types.GenerateVideosConfig(number_of_videos=1, resolution="720p")
        )
        while not ext_op.done:
            time.sleep(15)
            ext_op = client.operations.get(operation=ext_op)
        current_video = wait_for_active(ext_op.result.generated_videos[0].video)

    print("\n✅ 모든 비디오 연장 시퀀스 완료! 다운로드 시작...")
    file_name_part = "files/" + current_video.uri.split("files/")[-1].split(":")[0]

    # name 대신 file 키워드 매개변수 사용 (최신 SDK 대응)
    video_bytes = client.files.download(file=file_name_part)
    with open(output_filename, 'wb') as f:
        f.write(video_bytes)
    print(f"💾 로컬 다운로드 성공: {output_filename}")

if __name__ == "__main__":
    # 테스트 구동
    extend_prompts = [
        "The scene smoothly transitions as the subject takes a bite.",
        "A beautiful close-up showing the detail of the food."
    ]
    # generate_long_take("sample.jpg", "Cinematic master shot...", extend_prompts, "my_ad.mp4")
