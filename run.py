import sys
import json
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

from collector import collect_all


def main():
    print('=== YouTube 자동 수집 시작 ===')
    videos = collect_all()
    if not videos:
        print('[INFO] 수집된 영상 없음. 종료.')
        sys.exit(0)

    out_path = Path(__file__).parent / 'data' / 'videos.json'
    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(
        json.dumps(videos, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )
    print(f'[DONE] {len(videos)}개 → data/videos.json 저장 완료')


if __name__ == '__main__':
    main()
