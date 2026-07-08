# Job Scraper

국내 채용사이트(잡코리아, 사람인, 원티드, 점핏, 인크루트 등)에서 Java/Spring 백엔드 공고를 자동 수집합니다.

## Requirements

- Python 3.8+
- pip packages: `requests`, `beautifulsoup4`, `lxml`
- macOS (launchd 자동 실행 및 알림) / Windows (직접 실행)

## ⚠️ 중요: config.json 보안

`config.json`은 API 키 등 민감정보를 포함하므로 **git에 절대 커밋되지 않습니다** (`.gitignore`에 등록됨).
- 로컬에서 `config.example.json`을 복사해서 사용
- GitHub Actions에서는 workflow에서 자동 생성 (Secrets 사용)

## Quick Start

### macOS
```bash
cd job-scraper
bash setup.sh          # pip 설치 + config 생성 + launchd 등록
vim config.json        # 검색 조건 수정
python3 job_scraper.py              # 실제 실행
python3 job_scraper.py --dry-run    # 미리보기 (파일 변경 없음)
```

### Windows (PowerShell)
```powershell
# 1. 프로젝트 폴더로 이동
cd C:\Users\KIM\iCloudDrive\4.개인 자료\0.이력서\채용공고

# 2. 필수 패키지 설치
pip install requests beautifulsoup4 lxml

# 3. config.json 에서 검색 조건 수정

# 4. 수집 실행
python job_scraper.py              # 실제 실행
python job_scraper.py --dry-run    # 미리보기 (파일 변경 없음)
```

## Configuration

`config.example.json` → 복사해서 `config.json`으로 사용:

```json
{
  "output_dir": ".",
  "retention_days": 14,
  "notification": true,
  "max_per_site": 15,
  "company_info": true,
  "search": {
    "query": "Java Spring 백엔드 개발자",
    "career_level": "경력",
    "exclude_closed": true
  },
  "include_titles": ["java", "spring", "백엔드", "backend"],
  "exclude_titles": ["TOP100", "마케팅·홍보", "생산·제조"],
  "sites": {
    "jobkorea": { "enabled": true },
    "saramin": {
      "enabled": true,
      "category_code": "235"
    },
    "wanted": { "enabled": false },
    "jumpit": { "enabled": false },
    "incruit": { "enabled": false },
    "remember": { "enabled": false }
  }
}
```

| 항목 | 설명 |
|------|------|
| `output_dir` | 결과 파일(daily/, history.md) 저장 경로 |
| `notification` | 신규 공고 발견 시 macOS 알림 표시 |
| `max_per_site` | 사이트당 최대 수집 개수 |
| `company_info` | 기업정보(사원수/업종/기업구분) 수집 여부 (잡코리아만) |
| `search.query` | 검색어 (자유 텍스트, 사이트 검색 URL에 자동 반영) |
| `search.career_level` | `"경력"` / `"신입"` / `"전체"` |
| `search.career_from` | 최소 경력 연차 (예: `2` = 2년차 이상). 생략 시 필터 안 함 |
| `search.career_to` | 최대 경력 연차 (예: `5` = 5년차 이하). 생략 시 상한 없음 |
| `search.exclude_closed` | `true`: 마감된 공고 자동 제외 |
| `schedule.enabled` | `true`/`false` - launchd 자동 실행 활성화 (재실행: `bash setup.sh`) |
| `schedule.hour` | 자동 실행 시 (0~23) |
| `schedule.minute` | 자동 실행 분 (0~59) |
| `retention_days` | daily/ 파일 보관 일수 (초과 시 자동 삭제) |
| `include_titles` | 제목 필터 (빈 배열이면 필터 없음). 사용자 기술스택에 맞게 변경 |
| `exclude_titles` | 제목에서 제외할 키워드 |
| `profile` | 프로필명 (예: `"react"`, `"java"`). 설정 시 `daily/{profile}/` + `history.{profile}.md` 로 분리 저장 |
| `sites.*.enabled` | `true`/`false`로 각 사이트 활성화 |
| `saramin.category_code` | 사람인 직무 카테고리 코드 (235=Java, 84=웹개발) |

> `profile`을 설정하면 프로필별로 daily/history가 분리되므로, frontend/backend 등 여러 검색 조건을 동시에 운영 가능.
> CLI에서 `--profile java`로 오버라이드할 수도 있음.

### 검색 조건 커스터마이징 예시

React 프론트엔드 개발자(2년차)가 사용할 경우:

```json
{
    "search": {
      "query": "React Next.js 프론트엔드 개발자",
      "career_level": "경력",
      "career_from": 2,
      "career_to": 5,
      "exclude_closed": true
    },
  "include_titles": ["react", "next", "프론트엔드", "frontend", "typescript", "javascript"],
  "exclude_titles": ["Java", "Spring", "백엔드", ".NET", "C#"],
  "sites": {
    "jobkorea": { "enabled": true },
    "saramin": {
      "enabled": true,
      "category_code": "84"
    }
  }
}
```

> **잡코리아**: `search.query`가 검색 URL에 그대로 반영되어 자유 검색 가능.  
> **사람인**: `category_code`로 직무 카테고리 지정. 84=웹개발, 235=Java, 2=전체. 검색어(query)는 결과 내 필터링에 사용됨.

## Project Structure (초기 상태)

```
job-scraper/
├── config.example.json      # 설정 예제 (config.json으로 복사해서 사용)
├── job_scraper.py           # 메인 실행 스크립트
├── extractors/
│   ├── __init__.py          # 익스트랙터 레지스트리
│   ├── base.py              # 추상 클래스 + 공통 유틸
│   ├── jobkorea.py          # 잡코리아 (활성)
│   ├── saramin.py           # 사람인 (활성)
│   ├── wanted.py            # 원티드 (비활성)
│   ├── jumpit.py            # 점핏 (비활성)
│   ├── incruit.py           # 인크루트 (비활성)
│   └── remember.py          # 리멤버 (비활성)
├── setup.sh                 # 초기 설정 스크립트
├── com.opencode.jobscraper.plist  # [macOS] launchd 자동 실행 설정
└── README.md
```

실행 후 생성:
```
├── config.json              # 생성됨 (config.example.json → 복사)
├── daily/                   # 생성됨 (수집 결과)
│   ├── 2026-06-21.md
│   └── ...
└── history.md               # 생성됨 (최근 N일 통합)
```

## Adding a New Site

1. `extractors/` 디렉토리에 `mysite.py` 생성:

```python
from .base import BaseExtractor
from bs4 import BeautifulSoup

class MySiteExtractor(BaseExtractor):
    @property
    def name(self) -> str:
        return "mysite"

    def extract(self, config: dict) -> list[dict]:
        html = self.fetch("https://mysite.com/search?q=Java")
        if not html:
            return []
        soup = BeautifulSoup(html, "lxml")
        jobs = []
        for a in soup.select('a[href*="job"]'):
            href = self.make_absolute(a.get("href", ""), "https://mysite.com")
            title = self.clean_title(a.get_text(strip=True))
            jobs.append({
                "site": self.name,
                "title": title[:80],
                "url": href,
                "url_norm": self.normalize_url(href),
                # Optional: add these fields for richer output
                # "company": "...",
                # "deadline": "...",
                # "career": "...",
                # "tech_stack": ["Java", "Spring"],
                # "company_info": {"employees": "...", "industry": "..."},
            })
        return jobs
```

2. `extractors/__init__.py`에 등록:

```python
from .mysite import MySiteExtractor

EXTRACTORS = {
    ...
    "mysite": MySiteExtractor,
}
```

3. `config.json`의 `sites`에 추가.

## macOS Automation (launchd)

`setup.sh`가 자동 처리합니다. `config.json`에서 제어:

```json
"schedule": {
    "enabled": true,    // false면 launchd 등록 안 함
    "hour": 10,
    "minute": 0
}
```

설정 변경 후 `bash setup.sh` 재실행하면 plist가 자동 갱신 + 재등록됩니다.

```bash
# 상태 확인
launchctl list | grep jobscraper

# 로그 확인
tail -f /tmp/jobscraper.stdout.log
tail -f /tmp/jobscraper.stderr.log

# 수동 1회 실행
launchctl start com.jobscraper.daily

# 제거
launchctl unload ~/Library/LaunchAgents/com.jobscraper.daily.plist
```

## Commands

```bash
# 일반 실행 (신규 공고 → daily/ + history.md 갱신)
python3 job_scraper.py

# 미리보기 (파일 변경 없음)
python3 job_scraper.py --dry-run

# history.md만 재빌드 (daily/ 에서 재구성 + retention 초과 파일 정리)
python3 job_scraper.py --rebuild
```

## Output Format

daily/YYYY-MM-DD.md 파일은 다음 정보를 테이블로 출력합니다:

| 회사명 | 사이트 | 제목 | 경력 | 마감일 | 기술스택 | 기업정보 |
|------|------|-----|------|-------|---------|---------|

- **잡코리아**: ld+json에서 회사명/마감일/경력 추출. HTML body에서 기술스택(모집요강) 추출. 기업정보(사원수/업종/기업구분)는 detail 페이지 + 기업정보 더보기 페이지에서 추출 (`company_info: true` 설정 시)
- **사람인**: 검색 결과 `div.list_item` 구조에서 회사명/기술스택/경력/마감일/근무지 추출. 기업정보는 지원하지 않음 (detail 페이지가 SPA 구조)

## Site Status (2026-06-21 테스트 기준)

| 사이트 | 상태 | 비고 |
|--------|------|------|
| **잡코리아** | ✅ **활성** | 서버사이드 HTML + ld+json. detail + 기업정보 2회 추가 요청 |
| **사람인** | ✅ **활성** | 검색 결과 페이지만 파싱 (detail SPA). `category_code`로 직무 설정 |
| **원티드** | ✅ **활성** | Chaos API (`/api/chaos/navigation/v1/results`). 전체 개발 공고 중 제목 필터 매칭 |
| **점핏** | ❌ 비활성 | API JSON 파싱 실패 |
| **인크루트** | ❌ 비활성 | 검색 URL 404 |
| **리멤버** | ❌ 비활성 | DNS 조회 실패 (사이트 폐쇄) |

> `company_info: true`면 잡코리아 공고당 2회 추가 요청 → 실행 시간 증가

## GitHub Actions 자동화 (2026-07-08 추가)

매일 09:00 KST에 자동으로 스크래핑 → git commit/push → KakaoTalk 알림을 실행합니다.

### 설정 방법
1. GitHub repo → **Settings → Secrets and variables → Actions** 에 아래 등록:
   - `GH_PAT`: Personal Access Token (`repo` + `workflow` scope)
   - `KAKAO_REST_API_KEY`: Kakao Developers REST API 키
   - `KAKAO_REFRESH_TOKEN`: Kakao OAuth refresh token
2. 수동 실행: **Actions → Daily Job Scraper → Run workflow**

### 동작 흐름
```
09:00 KST → job_scraper.py 실행 → daily/*.md 생성
       → git commit + push (잔디 심김)
       → Kakao API (나에게 카톡 전송)
```

### 관련 프로젝트
- [kakao-bot](https://github.com/SungHoonGit/kakao-bot) — Kakao API 래퍼 + 웹훅 서버

## Notifications (알림)

신규 공고 발견 시 다양한 채널로 알림을 보낼 수 있습니다:

| 채널 | 설정 키 | 비고 |
|------|---------|------|
| **Email** | `notifications.channels.email` | SMTP with TLS (Gmail 권장) |
| **KakaoTalk** | `notifications.channels.kakao` | Kakao Developers REST API 필요 |
| **Telegram** | `notifications.channels.telegram` | BotFather에서 봇 생성 |

### Email 설정

```json
"email": {
  "enabled": true,
  "smtp_host": "smtp.gmail.com",
  "smtp_port": 587,
  "use_tls": true,
  "username": "your-email@gmail.com",
  "password": "앱비밀번호",
  "from_addr": "your-email@gmail.com",
  "to_addrs": ["recipient@example.com"]
}
```

> Gmail은 **앱 비밀번호** 필요: https://myaccount.google.com/apppasswords

### KakaoTalk 설정

1. [Kakao Developers](https://developers.kakao.com) 에서 앱 생성
2. **카카오 로그인** 활성화 → Redirect URI 에 `https://localhost` 등록
3. **카카오톡 메시지** API 활성화
4. **카카오 로그인** → **동의항목** → `카카오톡 메시지 전송` **필수 동의**
5. 액세스 토큰 발급 (아래 도우미 스크립트 실행):

```powershell
python scripts\get_kakao_token.py
```

→ 브라우저 로그인 → 리다이렉트 URL 복사 붙여넣기 → 자동 config 저장

```json
"kakao": {
  "enabled": true,
  "rest_api_key": "YOUR_REST_API_KEY",
  "access_token": "YOUR_ACCESS_TOKEN"
}
```

### Telegram 설정

1. [@BotFather](https://t.me/BotFather) 에서 봇 생성 → 토큰 발급
2. 봇과 대화 시작 후 `https://api.telegram.org/bot<TOKEN>/getUpdates` 에서 chat_id 확인

```json
"telegram": {
  "enabled": true,
  "bot_token": "YOUR_BOT_TOKEN",
  "chat_id": "YOUR_CHAT_ID"
}
```

### 환경변수 (선택)

민감한 정보는 `.env` 파일에 저장하고 `config.json`에서 `${VAR_NAME}` 참조 가능 (추후 구현).

## Project Structure (업데이트)

```
job-scraper/
├── config.json              # 설정 (notification 채널 포함)
├── .env.example             # 환경변수 템플릿 (비밀값)
├── job_scraper.py           # 메인 실행 스크립트
├── extractors/              # 채용사이트별 파서
├── notifiers/               # 알림 채널 모듈
│   ├── __init__.py          # JobAlert + 레지스트리
│   ├── console.py           # 콘솔 출력
│   ├── email_notifier.py    # SMTP TLS 이메일
│   ├── kakao_notifier.py    # 카카오톡 메시지
│   └── telegram_notifier.py # 텔레그램 봇
├── scripts/
│   └── get_kakao_token.py   # KakaoTalk OAuth 토큰 발급 도우미
├── .github/
│   └── workflows/
│       └── daily.yml        # GitHub Actions (매일 09:00 자동 실행)
└── README.md
```

## License

MIT
