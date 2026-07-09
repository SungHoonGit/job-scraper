# Job Scraper

국내 채용사이트(잡코리아, 사람인, 원티드 등)에서 프로필별(React/Java) 공고를 자동 수집합니다.

## Requirements

- Python 3.8+
- pip packages: `requests`, `beautifulsoup4`, `lxml`
- macOS (launchd 자동 실행 및 알림) / Windows (직접 실행)

## Quick Start

### 1. 저장소 클론 및 의존성 설치

```bash
git clone https://github.com/SungHoonGit/job-scraper.git
cd job-scraper
pip install requests beautifulsoup4 lxml
```

### 2. 프로필별 실행

설정 파일은 git에 포함되어 있습니다. `cp` 없이 `--config`로 바로 실행합니다.

```bash
# React 프로필
python3 job_scraper.py --config config.react.json

# Java 프로필
python3 job_scraper.py --config config.java.json

# 미리보기 (파일 변경 없음)
python3 job_scraper.py --config config.react.json --dry-run

# history만 재빌드
python3 job_scraper.py --config config.java.json --rebuild
```

### macOS (launchd 자동 실행)

```bash
bash setup.sh react    # 또는 setup.sh java
vim config.react.json  # 검색 조건/스케줄 수정 후 setup.sh 재실행
```

### Windows (PowerShell)

```powershell
cd C:\Users\KIM\git\job-scraper
pip install requests beautifulsoup4 lxml

python job_scraper.py --config config.react.json
python job_scraper.py --config config.java.json --dry-run
```

## Configuration

프로필별 설정 파일:

| 파일 | 프로필 | 용도 |
|------|--------|------|
| `config.react.json` | `react` | React/프론트엔드 검색 |
| `config.java.json` | `java` | Java/Spring 백엔드 검색 |

각 파일 예시 (`config.react.json`):

```json
{
  "output_dir": ".",
  "retention_days": 20,
  "notification": false,
  "max_per_site": 15,
  "company_info": false,
  "profile": "react",
  "search": {
    "query": "React Next.js TypeScript 프론트엔드 개발자 서울 경기",
    "career_level": "경력",
    "career_from": 2,
    "career_to": 2,
    "exclude_closed": true
  },
  "include_titles": ["react", "next", "프론트", "frontend", "typescript", "웹개발"],
  "exclude_titles": ["TOP100", "건설", "마케팅", "생산", "회계", "인사", "QA"],
  "sites": {
    "jobkorea": { "enabled": true },
    "saramin": { "enabled": true, "category_code": "84" },
    "wanted": { "enabled": true },
    "jumpit": { "enabled": false },
    "incruit": { "enabled": false },
    "remember": { "enabled": false }
  }
}
```

| 항목 | 설명 |
|------|------|
| `output_dir` | 결과 파일(`daily/`, `history.*.md`) 저장 경로 |
| `profile` | 프로필명. `daily/{profile}/` + `history.{profile}.md` 로 분리 저장 |
| `notification` | 신규 공고 발견 시 알림 (macOS 알림 또는 notifiers 채널) |
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
| `retention_days` | `daily/` 파일 보관 일수 (초과 시 자동 삭제) |
| `include_titles` | 제목 필터 (빈 배열이면 필터 없음) |
| `exclude_titles` | 제목에서 제외할 키워드 |
| `sites.*.enabled` | `true`/`false`로 각 사이트 활성화 |
| `saramin.category_code` | 사람인 직무 카테고리 코드 (235=Java, 84=웹개발) |

> `profile`은 config 파일과 `--profile` CLI 옵션 모두로 지정 가능. CLI가 우선합니다.

### 검색 조건 커스터마이징

React 프론트엔드 개발자(2년차) 예시는 `config.react.json`을, Java 백엔드(3~5년차) 예시는 `config.java.json`을 참고하세요.

> **잡코리아**: `search.query`가 검색 URL에 그대로 반영되어 자유 검색 가능.  
> **사람인**: `category_code`로 직무 카테고리 지정. 84=웹개발, 235=Java, 2=전체.

## Project Structure

```
job-scraper/
├── config.react.json        # React 프로필 설정 (git 포함)
├── config.java.json         # Java 프로필 설정 (git 포함)
├── job_scraper.py           # 메인 실행 스크립트
├── extractors/              # 채용사이트별 파서
├── notifiers/               # 알림 채널 모듈
├── scripts/
│   └── get_kakao_token.py   # KakaoTalk OAuth 토큰 발급 도우미
├── setup.sh                 # macOS 초기 설정 + launchd 등록
├── .github/workflows/
│   └── daily.yml            # GitHub Actions (매일 09:00 KST)
└── README.md
```

실행 후 생성:

```
├── daily/
│   ├── react/
│   │   └── 2026-07-09.md
│   └── java/
│       └── 2026-07-09.md
├── history.react.md
└── history.java.md
```

## Commands

```bash
python3 job_scraper.py --config config.react.json              # React 수집
python3 job_scraper.py --config config.java.json               # Java 수집
python3 job_scraper.py --config config.react.json --dry-run    # 미리보기
python3 job_scraper.py --config config.java.json --rebuild     # history 재빌드
python3 job_scraper.py --config config.react.json --profile react  # profile CLI 오버라이드
```

## Adding a New Site

1. `extractors/` 디렉토리에 `mysite.py` 생성
2. `extractors/__init__.py`에 등록
3. 각 `config.*.json`의 `sites`에 추가

## macOS Automation (launchd)

`setup.sh`가 자동 처리합니다. 해당 프로필 config에서 제어:

```json
"schedule": {
    "enabled": true,
    "hour": 10,
    "minute": 0
}
```

```bash
bash setup.sh react    # config.react.json 기준 launchd 등록
bash setup.sh java     # config.java.json 기준 launchd 등록

launchctl list | grep jobscraper
tail -f /tmp/jobscraper.stdout.log
launchctl start com.jobscraper.daily
```

## Output Format

`daily/{profile}/YYYY-MM-DD.md` 파일은 다음 정보를 테이블로 출력합니다:

| 회사명 | 사이트 | 제목 | 경력 | 마감일 | 기술스택 | 기업정보 |

## Site Status

| 사이트 | 상태 | 비고 |
|--------|------|------|
| **잡코리아** | ✅ **활성** | 서버사이드 HTML + ld+json |
| **사람인** | ✅ **활성** | 검색 결과 페이지 파싱. `category_code`로 직무 설정 |
| **원티드** | ✅ **활성** | Chaos API. 제목 필터 매칭 |
| **점핏** | ❌ 비활성 | API JSON 파싱 실패 |
| **인크루트** | ❌ 비활성 | 검색 URL 404 |
| **리멤버** | ❌ 비활성 | DNS 조회 실패 |

## GitHub Actions 자동화

매일 09:00 KST에 React/Java 프로필을 순차 실행 → git commit/push 합니다.

### 설정 방법

1. GitHub repo → **Settings → Secrets and variables → Actions** 에 등록:
   - `GH_PAT`: Personal Access Token (`repo` + `workflow` scope)
2. 수동 실행: **Actions → Daily Job Scraper → Run workflow**

### 동작 흐름

```
09:00 KST
  → python job_scraper.py --config config.react.json
  → python job_scraper.py --config config.java.json
  → git commit + push
```

설정 파일은 repo의 `config.react.json`, `config.java.json`을 그대로 사용합니다 (워크플로에서 `cp` 또는 inline 생성 없음).

## Notifications (알림)

신규 공고 발견 시 다양한 채널로 알림을 보낼 수 있습니다:

| 채널 | 설정 키 | 비고 |
|------|---------|------|
| **Email** | `notification.channels.email` | SMTP with TLS |
| **KakaoTalk** | `notification.channels.kakao` | Kakao Developers REST API |
| **Telegram** | `notification.channels.telegram` | BotFather 봇 |

알림 API 키/토큰은 해당 `config.*.json`에 로컬에서만 추가하세요. 커밋 전 민감정보가 포함되지 않았는지 확인하세요.

### KakaoTalk 설정

```powershell
python scripts\get_kakao_token.py --config config.react.json
```

```json
"notification": {
  "enabled": true,
  "channels": {
    "kakao": {
      "enabled": true,
      "rest_api_key": "YOUR_REST_API_KEY",
      "access_token": "YOUR_ACCESS_TOKEN"
    }
  }
}
```

## License

MIT
