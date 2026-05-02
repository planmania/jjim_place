import json
import os
import sys
from dotenv import load_dotenv
load_dotenv()

from collector import collect_all


def main():
    print('=== YouTube 자동 수집 시작 ===')
    videos = collect_all()
    if not videos:
        print('[INFO] 수집된 영상 없음. 종료.')
        sys.exit(0)

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'videos.json')
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(videos, f, ensure_ascii=False, indent=2)

    print(f'[DONE] data/videos.json 저장 완료 ({len(videos)}개)')


if __name__ == '__main__':
    main()
