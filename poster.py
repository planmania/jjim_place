import json
import re
import requests
from Crypto.Cipher import AES
from urllib.parse import urlparse
from config import INSERT_ENDPOINT, INSERT_TOKEN


def _solve_cupid(session: requests.Session, html: str, root_url: str, domain: str) -> bool:
    """CUPID 챌린지 해결 후 session 쿠키에 설정"""
    m = re.search(
        r'a=toNumbers\("([0-9a-f]+)"\),b=toNumbers\("([0-9a-f]+)"\),c=toNumbers\("([0-9a-f]+)"\)',
        html,
    )
    if not m:
        print('[WARN] CUPID 파라미터 파싱 실패')
        return False

    key = bytes.fromhex(m.group(1))
    iv  = bytes.fromhex(m.group(2))
    ct  = bytes.fromhex(m.group(3))
    result_hex = AES.new(key, AES.MODE_CBC, iv).decrypt(ct).hex()

    # cupid.js에서 쿠키 이름 확인
    try:
        cjs = session.get(root_url + '/cupid.js', timeout=10).text
        cn  = re.search(r'document\.cookie\s*=\s*["\']([^"\'=]+)=', cjs)
        if cn:
            name, value = cn.group(1).strip(), result_hex
        else:
            name, value = result_hex, '1'
    except Exception as e:
        print(f'[WARN] cupid.js 조회 실패: {e}')
        name, value = result_hex, '1'

    print(f'[INFO] CUPID 해결: {name[:32]}={value[:16]}...')
    session.cookies.set(name, value, domain=domain, path='/')
    return True


def post_to_cafe24(videos: list) -> dict:
    if not INSERT_ENDPOINT:
        print('[WARN] CAFE24_INSERT_URL 미설정 — dry_run 모드 (DB 미저장)')
        for v in videos:
            print(f'  {v["youtube_url"]}  {v["title"][:60]}')
        return {'success': True, 'inserted': 0, 'skipped': 0, 'errors': [], 'dry_run': True}

    parsed   = urlparse(INSERT_ENDPOINT)
    root_url = f"{parsed.scheme}://{parsed.netloc}"
    domain   = parsed.netloc
    session  = requests.Session()
    resp     = None

    # ── Step 1: 루트 도메인 GET으로 세션 워밍업 (CUPID 선제 해결) ──
    try:
        warmup = session.get(root_url, timeout=30, allow_redirects=True)
        if 'cupid.js' in warmup.text:
            print('[INFO] 워밍업 중 CUPID 감지 → 해결...')
            _solve_cupid(session, warmup.text, root_url, domain)
            warmup2 = session.get(root_url, timeout=30, allow_redirects=True)
            if 'cupid.js' in warmup2.text:
                print('[WARN] 워밍업 CUPID 재시도...')
                _solve_cupid(session, warmup2.text, root_url, domain)
        print(f'[INFO] 워밍업 완료 — 쿠키: {dict(session.cookies)}')
    except Exception as e:
        print(f'[WARN] 워밍업 실패 (무시): {e}')

    # ── Step 2: POST ──────────────────────────────────────────────
    body = json.dumps({'videos': videos}, ensure_ascii=False).encode('utf-8')
    hdrs = {
        'Content-Type': 'application/json; charset=utf-8',
        'X-Insert-Token': INSERT_TOKEN,
    }

    try:
        resp = session.post(INSERT_ENDPOINT, data=body, headers=hdrs, timeout=120)
        resp.raise_for_status()

        if 'cupid.js' in resp.text:
            print('[INFO] POST 중 CUPID 감지 → 해결 후 재시도...')
            _solve_cupid(session, resp.text, root_url, domain)
            resp = session.post(INSERT_ENDPOINT, data=body, headers=hdrs, timeout=120)
            resp.raise_for_status()

        return resp.json()

    except requests.exceptions.HTTPError as e:
        try:
            print(f'[ERROR] HTTP {resp.status_code}: {resp.text[:300]}')
        except Exception:
            pass
        return {'success': False, 'error': str(e)}
    except Exception as e:
        try:
            print(f'[DEBUG] 서버 응답 raw: {repr(resp.text[:500]) if resp is not None else "no response"}')
        except Exception:
            pass
        print(f'[ERROR] POST 실패: {e}')
        return {'success': False, 'error': str(e)}
