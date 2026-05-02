import re
from googleapiclient.discovery import build
import os
from config import YOUTUBE_API_KEY, KEYWORD_CONFIG, MAX_RESULTS_PER_KEYWORD, MIN_VIEW_COUNT


def build_youtube():
    return build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)


def search_videos(youtube, keyword: str) -> list:
    """키워드로 YouTube 동영상 검색 (조회수 순, 한국어)"""
    try:
        resp = youtube.search().list(
            part='id,snippet',
            q=keyword,
            type='video',
            order='viewCount',
            relevanceLanguage='ko',
            regionCode='KR',
            maxResults=MAX_RESULTS_PER_KEYWORD,
        ).execute()
    except Exception as e:
        print(f'[ERROR] search "{keyword}": {e}')
        return []

    ids = [item['id']['videoId'] for item in resp.get('items', [])]
    if not ids:
        return []

    try:
        detail = youtube.videos().list(
            part='snippet,statistics,contentDetails',
            id=','.join(ids),
        ).execute()
    except Exception as e:
        print(f'[ERROR] videos.list "{keyword}": {e}')
        return []

    results = []
    for item in detail.get('items', []):
        stats   = item.get('statistics', {})
        snippet = item['snippet']
        cd      = item.get('contentDetails', {})

        view_count = int(stats.get('viewCount', 0))
        if view_count < MIN_VIEW_COUNT:
            continue

        vid_id = item['id']

        # 썸네일: maxres → standard → high 순으로 최고화질 선택
        thumbs = snippet.get('thumbnails', {})
        thumb_url = (
            thumbs.get('maxres', {}).get('url') or
            thumbs.get('standard', {}).get('url') or
            thumbs.get('high', {}).get('url') or
            f'https://img.youtube.com/vi/{vid_id}/hqdefault.jpg'
        )

        # 재생 시간 (ISO 8601: PT4M13S)
        duration_iso = cd.get('duration', '')

        # 숏폼 판별: 3분 이하
        is_short = _iso_to_seconds(duration_iso) <= 180

        # 채널 태그 (최대 5개)
        yt_tags = snippet.get('tags', [])[:5]

        results.append({
            'video_id':     vid_id,
            'title':        snippet['title'],
            'channel':      snippet['channelTitle'],
            'channel_id':   snippet.get('channelId', ''),
            'description':  snippet.get('description', ''),   # 전문 — PHP에서 절삭
            'view_count':   view_count,
            'like_count':   int(stats.get('likeCount', 0)),
            'comment_count':int(stats.get('commentCount', 0)),
            'published_at': snippet['publishedAt'][:10],
            'youtube_url':  f'https://youtu.be/{vid_id}',
            'thumbnail_url':thumb_url,
            'duration_iso': duration_iso,
            'is_short':     is_short,
            'yt_tags':      yt_tags,
        })
    return results


def _iso_to_seconds(iso: str) -> int:
    """PT1H4M13S → 초 단위 정수"""
    m = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', iso or '')
    if not m:
        return 0
    h, mi, s = int(m.group(1) or 0), int(m.group(2) or 0), int(m.group(3) or 0)
    return h * 3600 + mi * 60 + s


def collect_all() -> list:
    youtube  = build_youtube()
    all_vids = []
    seen     = set()

    max_kw = int(os.environ.get('MAX_KEYWORDS', 0)) or len(KEYWORD_CONFIG)
    keywords = list(KEYWORD_CONFIG.items())[:max_kw]

    for keyword, (ca_name, province_ko) in keywords:
        print(f'[INFO] 수집: {keyword}')
        videos = search_videos(youtube, keyword)
        new = 0
        for v in videos:
            if v['video_id'] in seen:
                continue
            seen.add(v['video_id'])
            tag_kw   = keyword.replace(' ', '')
            short_tag = ',숏폼' if v['is_short'] else ''
            yt_tag_str = (',' + ','.join(v['yt_tags'])) if v['yt_tags'] else ''
            v.update({
                'keyword':     keyword,
                'ca_name':     ca_name,
                'province_ko': province_ko or '',
                'tags':        f'{tag_kw},유튜브,{v["channel"]}{short_tag}{yt_tag_str}',
            })
            all_vids.append(v)
            new += 1
        print(f'  → {new}개 추가 ({len(videos)}개 검색됨)')

    print(f'[INFO] 총 {len(all_vids)}개 수집 완료 (중복 제외)')
    return all_vids
