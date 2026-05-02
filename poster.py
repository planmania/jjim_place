import json
import requests
from config import INSERT_ENDPOINT, INSERT_TOKEN


def post_to_cafe24(videos: list) -> dict:
    if not INSERT_ENDPOINT:
        print('[WARN] CAFE24_INSERT_URL 미설정 — dry_run 모드 (DB 미저장)')
        for v in videos:
            print(f'  {v["video_id"]}  {v["title"][:60]}')
        return {'success': True, 'inserted': 0, 'skipped': 0, 'errors': [], 'dry_run': True}

    print(f'[INFO] 업로드 중 → {INSERT_ENDPOINT}')
    try:
        resp = requests.post(
            INSERT_ENDPOINT,
            json={'videos': videos},
            headers={
                'Content-Type': 'application/json; charset=utf-8',
                'X-Insert-Token': INSERT_TOKEN,
            },
            timeout=120,
        )
        print(f'[DEBUG] HTTP {resp.status_code} / {len(resp.content)} bytes / {repr(resp.text[:300])}')
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.HTTPError as e:
        print(f'[ERROR] HTTP {resp.status_code}: {resp.text[:300]}')
        return {'success': False, 'error': str(e)}
    except Exception as e:
        print(f'[ERROR] POST 실패: {e}')
        return {'success': False, 'error': str(e)}
