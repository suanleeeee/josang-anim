"""
팬 타입 분류 + 팀 순위 추천
"""

# ── 팀 소개 문구 (이번 버전 미사용) ──────────────────────────────────────────
TEAM_VIBES: dict = {}

# ── 팬 타입 설명 ──────────────────────────────────────────────────────────────
_TYPE_DESCS = {
    "투수콤":   "마운드 위에서 분투하는 선수들의 모습이 보입니다.",
    "타자콤":   "공을 친 그들의 방망이가 외치는 승리의 함성이 들립니다.",
    "내야콤":   "옷에 묻어있는 흙이 그들의 열정을 보여줍니다.",
    "외야콤":   "가장 외로운 곳에서 가장 위험한 순간을 막는 선수들의 몸을 던지는 플레이가 보입니다.",
    "포수콤":   "가장 낮은 곳에서 가장 무거운 책임을 가진 선수의 뒷모습이 보입니다.",
    "유격콤":   "가장 많은 타구와 경쟁하는 흙이 묻은 유니폼의 펄럭거림이 보입니다.",
    "얼라콤":   "어떤 새싹은 그 누구보다 굳건한 거목의 잠재력을 가지고 있습니다.",
    "거포콤":   "그 선수의 등장으로 팬들의 마음도 경기의 흐름도 뒤바꾸는 모습이 보입니다.",
}


def _ops_era_base(p: dict) -> float:
    """OPS/ERA 기반 승리기여도 추정 (carry 선수, WAR 없을 때)."""
    if p["season_ops"] is not None:
        try:
            ops = float(p["season_ops"])
            if ops >= 0.950:   return 78
            elif ops >= 0.900: return 66
            elif ops >= 0.800: return 52
            elif ops >= 0.700: return 36
            else:              return 24
        except ValueError:
            pass
    if p["season_era"] is not None:
        try:
            era = float(p["season_era"])
            if era <= 2.00:   return 78
            elif era <= 2.80: return 66
            elif era <= 3.80: return 52
            elif era <= 4.80: return 36
            else:             return 24
        except ValueError:
            pass
    return 26


def _recent_form_bonus(p: dict) -> float:
    """최근 경기 폼 보정 (-8 ~ +10)."""
    games = p.get("recent_games", [])
    if not games:
        return 0.0

    avgs = []
    for g in games:
        try:
            avgs.append(float(g.get("AVG", 0)))
        except (ValueError, TypeError):
            pass
    if avgs:
        recent_avg = sum(avgs) / len(avgs)
        if recent_avg >= 0.380:   return 10
        elif recent_avg >= 0.300: return 5
        elif recent_avg >= 0.200: return 0
        else:                     return -8

    eras = []
    for g in games:
        try:
            val = g.get("ERA") or g.get("평균자책점")
            if val:
                eras.append(float(val))
        except (ValueError, TypeError):
            pass
    if eras:
        recent_era = sum(eras) / len(eras)
        if recent_era <= 1.50:   return 10
        elif recent_era <= 3.00: return 5
        elif recent_era <= 5.00: return 0
        else:                    return -8

    return 0.0


def _score_player(p: dict) -> float:
    """승리기여도 중심 급조팬지수 (0~100).

    1순위: WAR (승리기여도 직접 지표)
    2순위: OPS/ERA (스탯 데이터 있을 때)
    3순위: 스탯 없는 1군 선수 = 26점 기본
    최근 폼 보정: ±10점
    """
    if p["war"] is not None:
        try:
            war = float(p["war"])
            if war >= 3.0:   base = 88
            elif war >= 2.0: base = 74
            elif war >= 1.0: base = 58
            elif war >= 0.5: base = 42
            else:            base = 28
        except ValueError:
            base = _ops_era_base(p)
    else:
        base = _ops_era_base(p)

    return min(100.0, base + _recent_form_bonus(p))


def _build_team_reason(top_player: dict, team: str) -> str:
    """팀 추천 이유 문자열 생성."""
    if not top_player["is_carry"]:
        return f"화려한 스탯은 아니지만, {team}과의 인연은 분명 존재합니다."

    parts = []
    if top_player.get("season_ops"):
        parts.append(f"OPS {top_player['season_ops']}")
    if top_player.get("season_era"):
        parts.append(f"ERA {top_player['season_era']}")
    if top_player.get("war"):
        parts.append(f"WAR {top_player['war']}")
    games = top_player.get("recent_games", [])
    if games:
        parts.append(f"최근 {len(games)}경기 기록 보유")

    name = top_player.get("name", "")
    if parts:
        return f"{name} 선수가 {team}에서 활약 중 ({', '.join(parts)})."
    return f"{name} 선수가 {team} 1군에서 활약 중입니다."


def _classify_fan_types(players: list, top_player: dict = None) -> tuple:
    """
    등번호를 공유하는 선수들의 공통 특성을 분석.

    투수콤/타자콤/내야콤/외야콤: 전체 선수 분포 기반
    포수콤/유격콤/얼라콤/거포콤: 1위 팀 선수(top_player) 기준
    """
    if not players:
        return [], {}

    types = []
    probs: dict = {}
    pos_data = [p.get("position", "").strip() for p in players if p.get("position")]

    # ── 전체 분포 기반 ───────────────────────────────────────────
    if pos_data:
        n = len(pos_data)
        pitcher_kws  = ["투수"]
        infield_kws  = ["1루수", "2루수", "3루수", "유격수", "내야수"]
        outfield_kws = ["좌익수", "중견수", "우익수", "외야수"]

        pitch_n = sum(1 for p in pos_data if any(k in p for k in pitcher_kws))
        in_n    = sum(1 for p in pos_data if any(k in p for k in infield_kws))
        out_n   = sum(1 for p in pos_data if any(k in p for k in outfield_kws))

        if pitch_n / n >= 0.5:
            types.append("투수콤")
            probs["투수콤"] = round(pitch_n / n * 100)
        elif (n - pitch_n) / n >= 0.5:
            types.append("타자콤")
            probs["타자콤"] = round((n - pitch_n) / n * 100)

        if in_n >= 4 and in_n / n >= 0.35:
            types.append("내야콤")
            probs["내야콤"] = round(in_n / n * 100)
        elif out_n >= 4 and out_n / n >= 0.35:
            types.append("외야콤")
            probs["외야콤"] = round(out_n / n * 100)

    # ── 1위 선수 기반 ────────────────────────────────────────────
    if top_player:
        pos = top_player.get("position", "")
        if "포수" in pos:
            types.append("포수콤")
            probs["포수콤"] = 100
        elif "유격수" in pos:
            types.append("유격콤")
            probs["유격콤"] = 100

        age = top_player.get("age")
        if age is not None and age <= 25:
            types.append("얼라콤")
            probs["얼라콤"] = 100

        slg = top_player.get("season_slg")
        if slg is not None:
            try:
                if float(slg) >= 0.500:
                    types.append("거포콤")
                    probs["거포콤"] = 100
            except ValueError:
                pass

    return types, probs


_BASE_TYPES = {"타자콤", "투수콤"}

def _fan_type_desc(fan_types: list, jersey: int) -> str:
    if not fan_types:
        return "이 번호를 달고 있는 선수들의 특성을 분석했습니다."
    if len(fan_types) == 1:
        return _TYPE_DESCS.get(fan_types[0], "이 번호 선수들의 공통 특성입니다.")
    specific = [t for t in fan_types if t not in _BASE_TYPES]
    if len(specific) == 1:
        return _TYPE_DESCS.get(specific[0], "이 번호 선수들의 공통 특성입니다.")
    return "활약하는 선수들이 다양한 길로 향하네요!"


def build_recommendation(players: list) -> dict:
    """
    find_players_by_jersey() 결과로 추천 JSON 생성.

    반환:
        {
          jersey,
          teams: [{rank, team, team_desc, fan_index, fan_index_desc, reason}],
          fan_types: [],
          fan_type_desc: str
        }
    """
    if not players:
        return _fallback()

    jersey = players[0]["jersey"]

    # ── 팀별 최고 점수 계산 ─────────────────────────────────────
    team_scores: dict[str, tuple[float, dict]] = {}
    for p in players:
        s = _score_player(p)
        team = p["team"]
        if team not in team_scores or s > team_scores[team][0]:
            team_scores[team] = (s, p)

    sorted_teams = sorted(team_scores.items(), key=lambda x: x[1][0], reverse=True)

    # ── 상위 3팀 빌드 ───────────────────────────────────────────
    teams = []
    for team, (score, top_player) in sorted_teams[:3]:
        fan_index = round(score)
        if fan_index >= 80:
            fan_index_desc = "이 번호와의 인연은 거의 운명 수준입니다."
        elif fan_index >= 60:
            fan_index_desc = "이 번호 선수가 활약 중입니다."
        else:
            fan_index_desc = "강한 인연은 아니지만 문은 열려있습니다."

        teams.append({
            "team":           team,
            "fan_index":      fan_index,
            "fan_index_desc": fan_index_desc,
            "reason":         _build_team_reason(top_player, team),
        })

    # ── carry 여부 판단 ─────────────────────────────────────────
    no_carry = not any(p["is_carry"] for p in players)

    # ── 팬 타입 분석 (전체 분포 + 1위 선수 기반) ─────────────────
    top_player = sorted_teams[0][1][1] if sorted_teams else None
    fan_types, fan_type_probs = _classify_fan_types(players, top_player=top_player)
    fan_type_desc = _fan_type_desc(fan_types, jersey)

    return {
        "jersey":          jersey,
        "teams":           teams,
        "no_carry":        no_carry,
        "fan_types":       fan_types,
        "fan_type_probs":  fan_type_probs,
        "fan_type_desc":   fan_type_desc,
    }


def _fallback() -> dict:
    return {
        "jersey":          0,
        "teams":           [],
        "fan_types":       [],
        "fan_type_probs":  {},
        "fan_type_desc":   "1~99 사이의 번호를 입력해 주세요.",
    }
