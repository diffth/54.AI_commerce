import os
import json
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# 사용할 API의 범위 (동영상 업로드 권한 필요)
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
CLIENT_SECRETS_FILE = 'client_secrets.json'
TOKEN_FILE = 'token.json'

def get_authenticated_service():
    """유튜브 API 서비스에 접근할 수 있도록 OAuth2 인증을 받아 클라이언트를 생성합니다."""
    creds = None
    # 이전에 저장된 토큰 정보가 있는지 확인합니다.
    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        except Exception as e:
            print(f"[WARN] 토큰 파일({TOKEN_FILE})을 로드하는 도중 오류가 발생해 무시합니다: {e}")

    # 자격 증명이 유효하지 않거나 존재하지 않을 경우 새로 요청합니다.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("[INFO] 만료된 토큰을 갱신(Refresh)하는 중...")
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"[WARN] 토큰 갱신에 실패하여 새로운 로그인이 필요합니다: {e}")
                creds = None

        if not creds:
            if not os.path.exists(CLIENT_SECRETS_FILE):
                raise FileNotFoundError(
                    f"[ERROR] '{CLIENT_SECRETS_FILE}'이 존재하지 않습니다.\n"
                    "유튜브 API 업로드를 사용하시려면 Google Cloud Console에서 OAuth 2.0 클라이언트 ID를 생성한 뒤\n"
                    f"다운로드 받아 '{CLIENT_SECRETS_FILE}' 이름으로 저장해 주세요."
                )
            
            print("[INFO] 웹 브라우저를 통해 유튜브 로그인 인증을 진행합니다...")
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        # 토큰 정보를 로컬에 저장합니다.
        with open(TOKEN_FILE, 'w', encoding='utf-8') as token:
            token.write(creds.to_json())
            print(f"[OK] 새로운 토큰 정보를 '{TOKEN_FILE}'에 저장했습니다.")

    return build('youtube', 'v3', credentials=creds)

def upload_video(video_path, title, description, tags=None, category_id="22", privacy_status="private"):
    """로컬 비디오 파일을 유튜브 채널에 자동으로 업로드합니다."""
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"[ERROR] 업로드할 비디오 파일이 존재하지 않습니다: {video_path}")

    print(f"[INFO] 유튜브 업로드 준비 중: {video_path}")
    youtube = get_authenticated_service()

    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': tags or [],
            'categoryId': category_id
        },
        'status': {
            'privacyStatus': privacy_status,
            'selfDeclaredMadeForKids': False
        }
    }

    # 대용량 파일 전송을 위해 1MB씩 나누어 업로드(Resumable Upload)
    media = MediaFileUpload(video_path, chunksize=1024*1024, resumable=True)

    request = youtube.videos().insert(
        part=','.join(body.keys()),
        body=body,
        media_body=media
    )

    print(f"[INFO] 업로드를 시작합니다: {title}")
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"[INFO] 업로드 중... ({int(status.progress() * 100)}%)")

    print(f"[OK] 업로드 완료! 비디오 ID: {response['id']}")
    return response['id']

if __name__ == "__main__":
    # 테스트 구동 (실제 호출을 위해서는 client_secrets.json이 필요합니다.)
    try:
        get_authenticated_service()
    except Exception as e:
        print(f"\n[INFO] 유튜브 API 초기화 테스트 결과: {e}")
