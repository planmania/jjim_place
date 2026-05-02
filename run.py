import sys
from dotenv import load_dotenv
load_dotenv()

from collector import collect_all
from poster import post_to_cafe24


def main():
    print('=== YouTube 자동 수집 시작 ===')
    videos = collect_all()
    if not videos:
        print('[INFO] 수집된 영상 없음. 종료.')
        sys.exit(0)

    result = post_to_cafe24(videos)
    print(f'[DONE] 등록 {result.get("inserted", 0)}개 · '
          f'중복 {result.get("skipped", 0)}개 · '
          f'오류 {len(result.get("errors", []))}개')
    for e in result.get('errors', []):
        print(f'  [ERR] {e}')

    if not result.get('success') and not result.get('dry_run'):
        sys.exit(1)


if __name__ == '__main__':
    main()
