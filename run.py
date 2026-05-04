import sys
import json
import os
import requests
from dotenv import load_dotenv
load_dotenv()

from collector import collect_all

UPLOAD_URL   = os.environ.get('CAFE24_INSERT_URL', '')
UPLOAD_TOKEN = os.environ.get('CAFE24_INSERT_TOKEN', '')


def main():
    print('=== YouTube 자동 수집 시작 ===')
    videos = collect_all()
    if not videos:
        print('[INFO] 수집된 영상 없음. 종료.')
        sys.exit(0)

    if not UPLOAD_URL or not UPLOAD_TOKEN:
        print('[ERROR] CAFE24_INSERT_URL 또는 CAFE24_INSERT_TOKEN 미설정')
        sys.exit(1)

    print(f'[INFO] {len(videos)}개 영상 → Cafe24 전송 중...')
    try:
        resp = requests.post(
            UPLOAD_URL,
            headers={
                'X-Upload-Token': UPLOAD_TOKEN,
                'Content-Type': 'application/json; charset=utf-8',
            },
            data=json.dumps(videos, ensure_ascii=False).encode('utf-8'),
            timeout=60,
        )
    except Exception as e:
        print(f'[ERROR] HTTP 요청 실패: {e}')
        sys.exit(1)

    if b'cupid.js' in resp.content:
        print(f'[ERROR] Cafe24 CUPID 봇 차단 감지 (HTTP {resp.status_code})')
        sys.exit(1)

    try:
        result = resp.json()
    except Exception:
        print(f'[ERROR] 응답 파싱 실패: HTTP {resp.status_code} / {resp.text[:300]}')
        sys.exit(1)

    if result.get('success'):
        print(f'[DONE] 등록: {result["inserted"]}개, 스킵: {result["skipped"]}개, 총: {result["total"]}개')
    else:
        print(f'[ERROR] {result.get("error", "알 수 없는 오류")}')
        sys.exit(1)


if __name__ == '__main__':
    main()
