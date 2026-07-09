#!/usr/bin/env python3
"""
KakaoTalk OAuth 토큰 발급 도우미

사용법:
    python scripts/get_kakao_token.py --config config.react.json
    python scripts/get_kakao_token.py --config config.java.json
"""
import argparse
import json
import os
import sys
import webbrowser
from urllib.parse import urlparse, parse_qs

import requests

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)

PROFILE_CONFIGS = ["config.react.json", "config.java.json"]


def load_config(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def parse_args():
    parser = argparse.ArgumentParser(description="KakaoTalk OAuth token helper")
    parser.add_argument(
        "--config", "-c",
        help="Config JSON path (default: first existing profile config)",
    )
    return parser.parse_args()


def resolve_config_path(config_arg):
    if config_arg:
        path = config_arg if os.path.isabs(config_arg) else os.path.join(PROJECT_DIR, config_arg)
        if not os.path.isfile(path):
            print(f"Config file not found: {path}")
            sys.exit(1)
        return path

    for name in PROFILE_CONFIGS:
        path = os.path.join(PROJECT_DIR, name)
        if os.path.isfile(path):
            return path

    print("Config file not found. Use --config config.react.json")
    sys.exit(1)


def main():
    args = parse_args()
    cfg_path = resolve_config_path(args.config)

    cfg = load_config(cfg_path)
    nc = cfg.get("notification", {})
    channels = nc.get("channels", {}) if isinstance(nc, dict) else {}
    kakao_cfg = channels.get("kakao", {})
    rest_api_key = kakao_cfg.get("rest_api_key", "") or kakao_cfg.get("admin_key", "")

    if not rest_api_key:
        print("config.kakao.rest_api_key 가 설정되지 않았습니다.")
        print(f"먼저 {os.path.basename(cfg_path)} 에 rest_api_key 를 입력해주세요.")
        sys.exit(1)

    REDIRECT_URI = "https://localhost"

    # 2. 인증 URL 생성
    auth_url = (
        "https://kauth.kakao.com/oauth/authorize"
        f"?client_id={rest_api_key}"
        f"&redirect_uri={REDIRECT_URI}"
        "&response_type=code"
        "&scope=talk_message"
    )

    print("=" * 60)
    print("KakaoTalk OAuth 토큰 발급")
    print("=" * 60)
    print(f"\nREST API 키: {rest_api_key[:8]}...{rest_api_key[-4:]}")
    print(f"\n1. 브라우저가 열리면 카카오 로그인 후 '동의하고 계속하기'를 누르세요.")
    print(f"2. https://localhost 로 리다이렉트 됩니다 (페이지 없음 = 정상)")
    print(f"3. 주소창의 전체 URL을 복사해서 아래에 붙여넣으세요.\n")

    input("엔터를 누르면 브라우저가 열립니다...")
    webbrowser.open(auth_url)

    redirect_result = input("\n리다이렉트된 전체 URL을 붙여넣으세요:\n").strip()

    # 3. code 추출
    parsed = urlparse(redirect_result)
    params = parse_qs(parsed.query)
    code = params.get("code", [None])[0]

    if not code:
        print("URL에서 code를 찾을 수 없습니다. 전체 URL을 정확히 복사했는지 확인하세요.")
        sys.exit(1)

    print(f"\n인증 코드 획득 성공. 토큰 발급 중...")

    # 4. 토큰 발급
    token_url = "https://kauth.kakao.com/oauth/token"
    payload = {
        "grant_type": "authorization_code",
        "client_id": rest_api_key,
        "redirect_uri": REDIRECT_URI,
        "code": code,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    try:
        resp = requests.post(token_url, data=payload, headers=headers, timeout=15)
        result = resp.json()

        if resp.status_code != 200 or "access_token" not in result:
            print(f"토큰 발급 실패: {result}")
            sys.exit(1)

        access_token = result["access_token"]
        refresh_token = result.get("refresh_token", "")
        expires_in = result.get("expires_in", 0)

        print(f"\n✅ 액세스 토큰 발급 성공!")
        print(f"   만료: {expires_in}초 ({expires_in // 3600}시간)")
        print(f"   Refresh Token: {refresh_token[:20]}...")
        print()

        # 5. config 업데이트 (여러 config 파일)
        configs_to_update = [cfg_path]
        for name in PROFILE_CONFIGS:
            p = os.path.join(PROJECT_DIR, name)
            if p != cfg_path and os.path.exists(p):
                configs_to_update.append(p)

        for path in configs_to_update:
            data = load_config(path)
            nc2 = data.get("notification", {})
            if isinstance(nc2, dict) and "channels" in nc2:
                if "kakao" in nc2["channels"]:
                    data["notification"]["channels"]["kakao"]["access_token"] = access_token
                    data["notification"]["channels"]["kakao"]["admin_key"] = ""
                    save_config(path, data)
                    print(f"  → {os.path.basename(path)} 업데이트 완료")

        print(f"\n🎉 KakaoTalk 알림 설정 완료!")
        print(f"이제 job_scraper.py 를 실행하면 카톡으로 알림이 옵니다.")

    except Exception as e:
        print(f"토큰 발급 중 오류: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
