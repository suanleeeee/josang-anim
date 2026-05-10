"""
KBO 선수 데이터 스크래퍼
프로젝트: 당신의 조상은 아닙니다만 응원팀 정해드립니다
팀: 우린 조상은 아니고요...

데이터 출처:
  - 선수 명단/등번호/포지션/투타/생년월일:
      https://www.koreabaseball.com/Player/RegisterAll.aspx
  - 타자 시즌 성적 및 최근 경기 기록 (WAR 대용 지표 포함):
      https://www.koreabaseball.com/Record/Player/HitterBasic/Basic1.aspx
      https://www.koreabaseball.com/Record/Player/HitterDetail/Basic.aspx?playerId={id}
  - 투수 시즌 성적(ERA) 및 최근 경기 기록:
      https://www.koreabaseball.com/Record/Player/PitcherBasic/Basic1.aspx
      https://www.koreabaseball.com/Record/Player/PitcherDetail/Basic.aspx?playerId={id}
  - WAR 시즌 랭킹 (로그인 불필요):
      https://statiz.co.kr/  (메인 WAR TOP 10 테이블)

의존 패키지: requests, beautifulsoup4, lxml
"""

import re
import json
import time
import logging
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# ── 로깅 설정 ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── 상수 정의 ─────────────────────────────────────────────────────────────────

KBO_BASE = "https://www.koreabaseball.com"
STATIZ_BASE = "https://statiz.co.kr"

# KBO 공식 사이트 팀 코드 매핑
TEAM_CODES = {
    "KT 위즈":     "KT",
    "LG 트윈스":   "LG",
    "SSG 랜더스":  "SK",
    "삼성 라이온즈": "SS",
    "기아 타이거즈": "HT",
    "NC 다이노스":  "NC",
    "두산 베어스":  "OB",
    "롯데 자이언츠": "LT",
    "한화 이글스":  "HH",
    "키움 히어로즈": "WO",
}

# 출력 팀 표기 (RegisterAll 기준)
REGISTER_TEAM_NAMES = {
    "KT":  "KT 위즈",
    "LG":  "LG 트윈스",
    "SK":  "SSG 랜더스",
    "SS":  "삼성 라이온즈",
    "HT":  "기아 타이거즈",
    "NC":  "NC 다이노스",
    "OB":  "두산 베어스",
    "LT":  "롯데 자이언츠",
    "HH":  "한화 이글스",
    "WO":  "키움 히어로즈",
}

# RegisterAll 페이지에서 팀별 등장 순서 (코치 0번 기준)
REGISTER_ALL_TEAM_ORDER = ["KT", "LG", "SK", "SS", "HT", "NC", "OB", "LT", "HH", "WO"]

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
}

# ── 유틸리티 ──────────────────────────────────────────────────────────────────

def _get(url: str, params: dict = None, referer: str = KBO_BASE, timeout: int = 20) -> requests.Response:
    """GET 요청 래퍼 (공통 헤더 + 예외처리)"""
    headers = {**DEFAULT_HEADERS, "Referer": referer}
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=timeout)
        resp.encoding = "utf-8"
        return resp
    except requests.RequestException as e:
        logger.error("GET 실패 [%s]: %s", url, e)
        return None


def _post_kbo(url: str, data: dict, referer: str = KBO_BASE, timeout: int = 20) -> requests.Response:
    """KBO ASP.NET POST 요청 래퍼"""
    headers = {
        **DEFAULT_HEADERS,
        "Referer": referer,
        "Content-Type": "application/x-www-form-urlencoded",
    }
    try:
        resp = requests.post(url, data=data, headers=headers, timeout=timeout)
        resp.encoding = "utf-8"
        return resp
    except requests.RequestException as e:
        logger.error("POST 실패 [%s]: %s", url, e)
        return None


def _parse_age(birthdate_str: str) -> int:
    """'YYYY-MM-DD' 형식 생년월일 -> 만 나이 계산"""
    try:
        birth = datetime.strptime(birthdate_str, "%Y-%m-%d")
        today = datetime.today()
        return today.year - birth.year - (
            (today.month, today.day) < (birth.month, birth.day)
        )
    except Exception:
        return None


def _extract_viewstate(soup: BeautifulSoup) -> dict:
    """ASP.NET VIEWSTATE 등 hidden field 추출"""
    fields = {}
    for name in ["__VIEWSTATE", "__VIEWSTATEGENERATOR", "__EVENTVALIDATION"]:
        tag = soup.find("input", {"name": name})
        fields[name] = tag["value"] if tag else ""
    return fields


# ── 1단계: 전체 선수 명단 수집 ────────────────────────────────────────────────
# 출처: https://www.koreabaseball.com/Player/RegisterAll.aspx

def fetch_all_rosters() -> dict:
    """
    KBO 10개 구단 전체 선수 명단을 가져옵니다.

    반환값:
        {
          "KT 위즈": [
            {"jersey": "1", "name": "고영표", "position": "투수",
             "bat_throw": "우언우타", "birthdate": "1991-09-16", "age": 34},
            ...
          ],
          ...
        }
    """
    # 출처: https://www.koreabaseball.com/Player/RegisterAll.aspx
    url = f"{KBO_BASE}/Player/RegisterAll.aspx"
    logger.info("전체 선수 명단 수집 중: %s", url)

    resp = _get(url)
    if resp is None:
        logger.error("RegisterAll 페이지 요청 실패")
        return {}

    soup = BeautifulSoup(resp.text, "lxml")

    # RegisterAll 구조:
    #   <div class="playerRegist"> 가 팀별로 10개 존재 (KBO 공식 순서 그대로)
    #   각 div 안에 <table class="tData tDays"> 1개
    #     row 0: 헤더 — 구단 | 감독(n) | 코치(n) | 투수(n) | 포수(n) | 내야수(n) | 외야수(n)
    #     row 1: 데이터 — 팀명+인원 | 코칭스태프 | ... | 투수목록 | 포수목록 | 내야수목록 | 외야수목록
    #   팀 매핑: div 순서 = REGISTER_ALL_TEAM_ORDER 순서 (이름 검출 대신 위치 기반)
    # div.playerRegist 하나 안에 10개 팀 테이블이 모두 들어있음
    container = soup.find("div", class_="playerRegist")
    if container:
        team_tables = container.find_all("table", class_=lambda c: c and "tDays" in c)
    else:
        team_tables = soup.find_all("table", class_=lambda c: c and "tDays" in c)

    logger.info("발견된 팀 테이블 수: %d", len(team_tables))

    player_pattern = re.compile(r"([가-힣A-Za-z·・ㄱ-ㅎ]+)\((\d{1,3})\)")
    rosters = {}

    for idx, table in enumerate(team_tables):
        rows = table.find_all("tr")
        if not rows:
            continue

        header_cells = rows[0].find_all(["th", "td"])
        headers = [c.get_text(strip=True) for c in header_cells]

        # 첫 번째 데이터 셀에서 팀 추출 (예: "KT40명", "삼성39명", "롯데39명")
        _ABBR_MAP = {
            "KT":  "KT 위즈",
            "LG":  "LG 트윈스",
            "삼성": "삼성 라이온즈",
            "SSG": "SSG 랜더스",
            "KIA": "기아 타이거즈",
            "기아": "기아 타이거즈",
            "NC":  "NC 다이노스",
            "두산": "두산 베어스",
            "롯데": "롯데 자이언츠",
            "한화": "한화 이글스",
            "키움": "키움 히어로즈",
        }
        team_name = None
        if len(rows) > 1:
            first_cells = rows[1].find_all(["td", "th"])
            first_text = first_cells[0].get_text(strip=True) if first_cells else ""
            for abbr, name in _ABBR_MAP.items():
                if first_text.startswith(abbr):
                    team_name = name
                    break

        # 팀명 추출 실패 시 순서 기반 fallback
        if team_name is None:
            if idx >= len(REGISTER_ALL_TEAM_ORDER):
                break
            team_name = REGISTER_TEAM_NAMES[REGISTER_ALL_TEAM_ORDER[idx]]

        rosters[team_name] = []

        for row in rows[1:]:
            cells = row.find_all(["td", "th"])
            if not cells:
                continue

            # cells[0] = 팀명+인원 (예: "KT40명"), cells[1:] = 직책별 선수
            for col_idx, cell in enumerate(cells[1:], start=1):
                if col_idx >= len(headers):
                    break
                position_label = headers[col_idx].split("(")[0].strip()
                if position_label in ("감독", "코치"):
                    continue

                for m in player_pattern.finditer(cell.get_text(strip=True)):
                    rosters[team_name].append({
                        "jersey":   m.group(2),
                        "name":     m.group(1),
                        "position": position_label,
                    })

    logger.info("수집된 팀 수: %d", len(rosters))
    return rosters


# ── 2단계: 선수별 나이/투타 정보 보완 (Register.aspx 팀별) ───────────────────
# 출처: https://www.koreabaseball.com/Player/Register.aspx

def fetch_team_detail(team_code: str, session: requests.Session = None) -> list:
    """
    특정 팀의 선수별 상세 정보(등번호, 이름, 포지션, 투타유형, 생년월일)를 가져옵니다.

    Args:
        team_code: KBO 팀 코드 (예: "HT", "LG")
        session: 재사용할 requests.Session (없으면 새로 생성)

    반환값:
        [{"jersey": "7", "name": "김상수", "position": "내야수",
          "bat_throw": "우투우타", "birthdate": "1990-03-23", "age": 35}, ...]
    """
    # 출처: https://www.koreabaseball.com/Player/Register.aspx
    url = f"{KBO_BASE}/Player/Register.aspx"

    if session is None:
        session = requests.Session()
        session.headers.update(DEFAULT_HEADERS)

    # 1) GET으로 초기 VIEWSTATE 획득 (기본 팀: KT)
    resp = session.get(url, timeout=20)
    resp.encoding = "utf-8"
    soup = BeautifulSoup(resp.text, "lxml")
    vs = _extract_viewstate(soup)

    team_name_input = soup.find("input", {"name": lambda n: n and "hfSearchTeam" in str(n)})
    date_input = soup.find("input", {"name": lambda n: n and "hfSearchDate" in str(n)})

    team_field_name = team_name_input["name"] if team_name_input else \
        "ctl00$ctl00$ctl00$cphContents$cphContents$cphContents$hfSearchTeam"
    date_field_name = date_input["name"] if date_input else \
        "ctl00$ctl00$ctl00$cphContents$cphContents$cphContents$hfSearchDate"
    current_date = date_input["value"] if date_input else datetime.today().strftime("%Y%m%d")

    # 2) POST로 팀 전환
    post_data = {
        "__EVENTTARGET": team_field_name,
        "__EVENTARGUMENT": "",
        **vs,
        team_field_name: team_code,
        date_field_name: current_date,
    }
    resp2 = session.post(
        url,
        data=post_data,
        headers={"Content-Type": "application/x-www-form-urlencoded", "Referer": url},
        timeout=20,
    )
    resp2.encoding = "utf-8"
    soup2 = BeautifulSoup(resp2.text, "lxml")

    # 3) tNData 테이블 파싱
    players = []
    position_map = {
        "감독": "감독", "코치": "코치",
        "투수": "투수", "포수": "포수",
        "내야수": "내야수", "외야수": "외야수",
    }

    for table in soup2.find_all("table", class_="tNData"):
        header_row = table.find("tr")
        if not header_row:
            continue
        header_cells = header_row.find_all(["th", "td"])
        if not header_cells:
            continue

        # 두 번째 컬럼이 포지션 레이블
        pos_label = header_cells[1].get_text(strip=True) if len(header_cells) > 1 else ""
        if pos_label in ("감독", "코치"):
            continue

        for row in table.find_all("tr")[1:]:
            cells = row.find_all(["td", "th"])
            if len(cells) < 4:
                continue
            jersey     = cells[0].get_text(strip=True)
            name       = cells[1].get_text(strip=True)
            bat_throw  = cells[2].get_text(strip=True)
            birthdate  = cells[3].get_text(strip=True)
            age        = _parse_age(birthdate)

            players.append({
                "jersey":    jersey,
                "name":      name,
                "position":  pos_label,
                "bat_throw": bat_throw,
                "birthdate": birthdate,
                "age":       age,
            })

    return players


# ── 3단계: KBO 기록 페이지에서 캐리 선수 목록 수집 ────────────────────────────
# 출처: https://www.koreabaseball.com/Record/Player/HitterBasic/Basic1.aspx (AVG 순위)
#       https://www.koreabaseball.com/Record/Player/HitterBasic/Basic2.aspx (OPS 포함)
#       https://www.koreabaseball.com/Record/Player/PitcherBasic/Basic1.aspx (ERA 순위)
#
# ▶ 설계 원칙
#   팀 필터 POST는 KBO ASP.NET 세션 문제로 동작하지 않으므로 GET만 사용.
#   탑 랭킹 페이지에 이름이 등장하는 선수 = "캐리 선수(is_carry=True)".
#   캐리 선수만 player_id / 최근 경기 데이터를 수집하며, 나머지는 기본 정보만 반환.

def _parse_stats_table(soup: BeautifulSoup, stat_keys: "str | list[str]") -> dict:
    """
    KBO 기록 페이지 테이블에서 {선수명: {player_id, team_code, <stat_key>: 값, ...}} 추출.

    stat_keys: 단일 문자열 또는 리스트 (예: 'era', ['ops', 'slg'])
    """
    if isinstance(stat_keys, str):
        stat_keys = [stat_keys]

    table = soup.find("table")
    if not table:
        return {}

    rows = table.find_all("tr")
    if not rows:
        return {}

    headers = [th.get_text(strip=True) for th in rows[0].find_all(["th", "td"])]
    key_indices = {key: headers.index(key.upper()) for key in stat_keys if key.upper() in headers}

    result = {}
    for row in rows[1:]:
        link = row.find("a", href=lambda h: h and "playerId=" in str(h))
        if not link:
            continue
        player_id   = link["href"].split("playerId=")[-1].strip()
        player_name = link.get_text(strip=True)
        cells       = row.find_all(["td", "th"])
        team_code   = cells[2].get_text(strip=True) if len(cells) > 2 else ""

        entry = {"player_id": player_id, "team_code": team_code}
        for key, idx in key_indices.items():
            entry[key] = cells[idx].get_text(strip=True) if idx < len(cells) else None

        result[player_name] = entry
    return result


def build_kbo_stats_map() -> dict:
    """
    KBO 1군 타자(OPS)·투수(ERA) 탑 랭킹을 GET으로 수집해 통합 맵을 반환합니다.

    carry 판별 기준: 타자 OPS 랭킹 등장 여부 / 투수 ERA 랭킹 등장 여부.
    AVG 랭킹은 사용하지 않음 (승리기여도와 무관한 안타 제조기 포함 방지).

    반환값:
        {
          "박성한": {"player_id": "67893", "team_code": "SK",
                     "ops": "1.009", "era": None, "is_pitcher": False},
          "후라도": {"player_id": "...",   "team_code": "NC",
                     "ops": None,    "era": "2.00", "is_pitcher": True},
          ...
        }
    """
    hitter_url_ops = f"{KBO_BASE}/Record/Player/HitterBasic/Basic2.aspx"
    pitcher_url    = f"{KBO_BASE}/Record/Player/PitcherBasic/Basic1.aspx"

    logger.info("KBO 탑 랭킹 수집 중 (타자 OPS, 투수 ERA)")

    # 타자 - Basic2: OPS + SLG (carry 기준)
    resp_ops = _get(hitter_url_ops)
    hitter_ops_map = _parse_stats_table(
        BeautifulSoup(resp_ops.text, "lxml"), ["ops", "slg"]
    ) if resp_ops else {}
    time.sleep(0.5)

    # 투수 - Basic1: ERA (carry 기준)
    resp_era = _get(pitcher_url)
    pitcher_map = _parse_stats_table(
        BeautifulSoup(resp_era.text, "lxml"), "era"
    ) if resp_era else {}

    # 통합: 타자
    combined = {}
    for name, info in hitter_ops_map.items():
        combined[name] = {
            "player_id":  info["player_id"],
            "team_code":  info["team_code"],
            "ops":        info.get("ops"),
            "slg":        info.get("slg"),
            "era":        None,
            "is_pitcher": False,
        }

    # 통합: 투수
    for name, info in pitcher_map.items():
        combined[name] = {
            "player_id":  info["player_id"],
            "team_code":  info["team_code"],
            "ops":        None,
            "era":        info.get("era"),
            "is_pitcher": True,
        }

    logger.info("KBO 탑 랭킹 수집 완료: 타자 %d명 / 투수 %d명",
                len(hitter_ops_map), len(pitcher_map))
    return combined


# ── 4단계: 선수 최근 N경기 성적 수집 ─────────────────────────────────────────
# 출처:
#   타자: https://www.koreabaseball.com/Record/Player/HitterDetail/Basic.aspx?playerId={id}
#   투수: https://www.koreabaseball.com/Record/Player/PitcherDetail/Basic.aspx?playerId={id}

def fetch_recent_games(player_id: str, is_pitcher: bool, n: int = 5) -> list:
    """
    선수 상세 페이지에서 최근 n경기 기록을 가져옵니다.

    타자: 날짜, 상대, AVG, PA, H, HR, RBI 반환
    투수: 날짜, 상대, ERA_game, IP, ER, SO 반환

    수집 실패 시 빈 리스트 반환.
    """
    if is_pitcher:
        # 출처: https://www.koreabaseball.com/Record/Player/PitcherDetail/Basic.aspx
        url = f"{KBO_BASE}/Record/Player/PitcherDetail/Basic.aspx?playerId={player_id}"
    else:
        # 출처: https://www.koreabaseball.com/Record/Player/HitterDetail/Basic.aspx
        url = f"{KBO_BASE}/Record/Player/HitterDetail/Basic.aspx?playerId={player_id}"

    resp = _get(url)
    if resp is None:
        return []

    try:
        soup = BeautifulSoup(resp.text, "lxml")
        tables = soup.find_all("table")

        # 최근 경기 테이블: 헤더에 '일자' 또는 '날짜' 포함된 테이블
        game_table = None
        for t in tables:
            header_texts = [th.get_text(strip=True) for th in t.find_all(["th", "td"])[:3]]
            if "일자" in header_texts or "날짜" in header_texts or "상대" in header_texts:
                game_table = t
                break

        if not game_table:
            return []

        rows = game_table.find_all("tr")
        if len(rows) < 2:
            return []

        headers = [th.get_text(strip=True) for th in rows[0].find_all(["th", "td"])]
        games = []

        # 첫 행 = 헤더, 두 번째 행 = 합계(skip), 이후 = 경기별 데이터
        data_rows = rows[1:]
        # '합계' 행 제거
        data_rows = [r for r in data_rows
                     if "합계" not in r.get_text(strip=True)[:4]]

        for row in data_rows[:n]:
            cells = row.find_all(["td", "th"])
            row_data = {
                h: cells[i].get_text(strip=True)
                for i, h in enumerate(headers)
                if i < len(cells)
            }
            games.append(row_data)

        return games

    except Exception as e:
        logger.warning("최근 경기 파싱 실패 (player_id=%s): %s", player_id, e)
        return []


# ── 5단계: 스탯티즈 WAR 데이터 수집 ──────────────────────────────────────────
# 출처: https://statiz.co.kr/  (메인 페이지 WAR TOP10 - 로그인 불필요)

def fetch_statiz_war() -> dict:
    """
    스탯티즈 메인 페이지에서 WAR TOP10 데이터를 가져옵니다.
    로그인이 필요한 상세 기록실 대신 메인 공개 데이터를 사용합니다.

    반환값:
        {"박성한": {"war": 2.61, "rank": 1}, "후라도": {"war": 2.27, "rank": 2}, ...}
    """
    # 출처: https://statiz.co.kr/ (메인 WAR TOP10 위젯)
    url = f"{STATIZ_BASE}/"
    logger.info("스탯티즈 WAR 데이터 수집 중: %s", url)

    resp = _get(url, referer=STATIZ_BASE)
    if resp is None:
        return {}

    try:
        soup = BeautifulSoup(resp.text, "lxml")
        war_map = {}

        # WAR 컬럼이 있는 테이블 찾기
        for table in soup.find_all("table"):
            header_row = table.find("tr")
            if not header_row:
                continue
            headers = [th.get_text(strip=True) for th in header_row.find_all(["th", "td"])]
            if "WAR" not in headers or "이름" not in headers:
                continue

            war_idx  = headers.index("WAR")
            name_idx = headers.index("이름")
            rank_idx = headers.index("순위") if "순위" in headers else None

            for row in table.find_all("tr")[1:]:
                cells = row.find_all(["td", "th"])
                if len(cells) <= max(war_idx, name_idx):
                    continue
                name = cells[name_idx].get_text(strip=True)
                try:
                    war_val = float(cells[war_idx].get_text(strip=True))
                except ValueError:
                    continue
                rank = int(cells[rank_idx].get_text(strip=True)) if rank_idx is not None else None

                war_map[name] = {"war": war_val, "rank": rank}

        logger.info("스탯티즈 WAR 수집 완료: %d명", len(war_map))
        return war_map

    except Exception as e:
        logger.error("스탯티즈 WAR 파싱 실패: %s", e)
        return {}


# ── 메인 함수: 등번호로 선수 조회 ─────────────────────────────────────────────

JERSEY_MIN = 0
JERSEY_MAX = 99


def _calc_iso(slg: str, avg: str):
    """ISO(순장타율) = SLG - AVG. 계산 불가 시 None 반환."""
    try:
        return round(float(slg) - float(avg), 3)
    except (ValueError, TypeError):
        return None


def find_players_by_jersey(jersey_number: str | int) -> list:
    """
    KBO 1군 10개 구단에서 해당 등번호(1~99)를 단 선수를 모두 찾습니다.

    탑 랭킹 페이지에 등장하는 선수 = 캐리 선수(is_carry=True).
    캐리 선수에 한해 player_id·시즌 성적·최근 5경기 기록을 수집합니다.
    WAR(스탯티즈 TOP10)은 보너스 데이터로 포함됩니다.

    Args:
        jersey_number: 조회할 등번호 (1~99)

    반환값:
        [
          {
            "jersey": "7",
            "name": "김주원",
            "team": "NC 다이노스",
            "team_code": "NC",
            "position": "내야수",
            "bat_throw": "우투우타",
            "birthdate": "2000-08-12",
            "age": 25,
            "is_carry": True,          # 탑 랭킹 등장 여부 (급조팬지수 핵심 지표)
            "player_id": "78901",
            "season_ops": "0.823",     # 타자, 캐리 선수만
            "season_era": None,        # 투수, 캐리 선수만
            "war": None,               # 스탯티즈 TOP10 선수만
            "recent_games": [...]      # 캐리 선수만
          },
          ...
        ]
    """
    target_jersey = str(jersey_number).strip()
    jersey_int = int(target_jersey) if target_jersey.isdigit() else -1

    if jersey_int < JERSEY_MIN or jersey_int > JERSEY_MAX:
        logger.warning(
            "등번호 %s는 지원 범위(%d~%d)를 벗어납니다.",
            target_jersey, JERSEY_MIN, JERSEY_MAX,
        )
        return []

    logger.info("등번호 %s 선수 조회 시작 (1군 한정)", target_jersey)

    # ── 1) 전체 선수 명단 (RegisterAll) ──
    all_rosters = fetch_all_rosters()
    if not all_rosters:
        logger.error("선수 명단 수집 실패")
        return []

    matched_basic = [
        {**p, "team": team_name}
        for team_name, players in all_rosters.items()
        for p in players
        if p["jersey"] == target_jersey
    ]

    logger.info("등번호 %s 매칭: %d명", target_jersey, len(matched_basic))
    if not matched_basic:
        logger.warning("등번호 %s 선수를 찾지 못했습니다.", target_jersey)
        return []

    # ── 2) KBO 탑 랭킹 (캐리 선수 판별 + player_id + 시즌 성적) ──
    time.sleep(0.3)
    stats_map = build_kbo_stats_map()

    # ── 3) WAR 데이터 (스탯티즈 TOP10, 보너스) ──
    time.sleep(0.3)
    war_data = fetch_statiz_war()

    # ── 4) 각 선수별 상세 수집 ──
    result = []
    detail_session = requests.Session()
    detail_session.headers.update(DEFAULT_HEADERS)

    # 팀 상세(Register.aspx)는 팀별로 한 번만 요청
    team_detail_cache: dict[str, list] = {}

    for basic in matched_basic:
        team_full   = basic["team"]
        player_name = basic["name"]
        position    = basic["position"]

        team_code = next(
            (code for full, code in TEAM_CODES.items() if full == team_full),
            ""
        )

        logger.info("  처리 중: %s (%s / %s)", player_name, team_full, position)

        # 4-1) 팀 상세 (투타, 생년월일) — 팀당 1회 캐시
        if team_code not in team_detail_cache:
            time.sleep(0.5)
            try:
                team_detail_cache[team_code] = fetch_team_detail(
                    team_code, session=detail_session
                )
            except Exception as e:
                logger.warning("팀 상세 수집 실패 (%s): %s", team_full, e)
                team_detail_cache[team_code] = []

        detail_info = next(
            (p for p in team_detail_cache[team_code] if p["name"] == player_name),
            {}
        )

        # 4-2) 캐리 여부 판별
        stat_info  = stats_map.get(player_name, {})
        is_carry   = bool(stat_info)
        player_id  = stat_info.get("player_id")
        is_pitcher = stat_info.get("is_pitcher", position == "투수")

        # 4-3) 최근 5경기 (캐리 선수만)
        recent_games = []
        if is_carry and player_id:
            time.sleep(0.5)
            try:
                recent_games = fetch_recent_games(
                    player_id, is_pitcher=is_pitcher, n=5
                )
            except Exception as e:
                logger.warning("최근 경기 수집 실패 (%s): %s", player_name, e)

        # 4-4) WAR (스탯티즈 보너스)
        war_info = war_data.get(player_name, {})

        result.append({
            "jersey":       target_jersey,
            "name":         player_name,
            "team":         team_full,
            "team_code":    team_code,
            "position":     detail_info.get("position", position),
            "bat_throw":    detail_info.get("bat_throw", ""),
            "birthdate":    detail_info.get("birthdate", ""),
            "age":          detail_info.get("age"),
            "is_carry":     is_carry,
            "player_id":    player_id,
            "season_ops":   stat_info.get("ops") if not is_pitcher else None,
            "season_slg":   stat_info.get("slg") if not is_pitcher else None,
            "season_era":   stat_info.get("era") if is_pitcher else None,
            "war":          war_info.get("war"),
            "recent_games": recent_games,
        })
        time.sleep(0.3)

    logger.info("등번호 %s 조회 완료: %d명 (캐리 %d명)",
                target_jersey, len(result),
                sum(1 for p in result if p["is_carry"]))
    return result


# ── JSON 저장 함수 ─────────────────────────────────────────────────────────────

def save_to_json(data: list | dict, jersey_number: str | int = None,
                 output_dir: str = None) -> str:
    """
    수집한 데이터를 JSON 파일로 저장합니다.

    Args:
        data:          저장할 데이터 (리스트 또는 딕셔너리)
        jersey_number: 등번호 (파일명에 사용)
        output_dir:    저장 경로 (기본: 스크립트 위치)

    반환값:
        저장된 파일의 절대 경로 문자열
    """
    if output_dir is None:
        output_dir = Path(__file__).parent
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if jersey_number is not None:
        filename = f"jersey_{jersey_number}_{timestamp}.json"
    else:
        filename = f"kbo_data_{timestamp}.json"

    filepath = output_dir / filename

    payload = {
        "collected_at": datetime.now().isoformat(),
        "jersey_number": str(jersey_number) if jersey_number is not None else None,
        "total_players": len(data) if isinstance(data, list) else None,
        "players": data,
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    logger.info("JSON 저장 완료: %s", filepath)
    return str(filepath)


# ── 진입점 ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    jersey = sys.argv[1] if len(sys.argv) > 1 else "7"
    print(f"\n{'='*60}")
    print(f"  KBO 1군 등번호 {jersey}번 선수 조회 (범위: {JERSEY_MIN}~{JERSEY_MAX})")
    print(f"{'='*60}\n")

    players = find_players_by_jersey(jersey)

    if not players:
        print(f"해당 등번호 선수를 찾지 못했습니다. (지원 범위: {JERSEY_MIN}~{JERSEY_MAX})")
        sys.exit(0)

    carry = [p for p in players if p["is_carry"]]
    print(f"총 {len(players)}명 발견 / 캐리 선수: {len(carry)}명\n")

    for p in players:
        carry_tag = "★캐리" if p["is_carry"] else "  "
        print(f"  {carry_tag} [{p['team']}] {p['name']} (#{p['jersey']})")
        print(f"    포지션: {p['position']} | 투타: {p['bat_throw']} | 나이: {p['age']}세 ({p['birthdate']})")
        if p["season_era"] is not None:
            print(f"    시즌 ERA: {p['season_era']}")
        if p["season_ops"] is not None:
            print(f"    시즌 OPS: {p['season_ops']}")
        if p["war"] is not None:
            print(f"    WAR: {p['war']} (스탯티즈 TOP10)")
        if p["recent_games"]:
            print(f"    최근 {len(p['recent_games'])}경기:")
            for g in p["recent_games"]:
                items = " | ".join(f"{k}:{v}" for k, v in list(g.items())[:6])
                print(f"      {items}")
        print()

    out_dir = Path(__file__).parent
    saved_path = save_to_json(players, jersey_number=jersey, output_dir=str(out_dir))
    print(f"JSON 저장 완료: {saved_path}")
