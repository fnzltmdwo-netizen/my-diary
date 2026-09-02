"""IU Brain v4.7 — checking urge / envy / comparison / attention-return layer.

Builds on v4.6 anger-release. This layer improves retrieval and prompting for
repeated digital checking, reassurance-seeking, envy, comparison, and returning
attention to the user's own life.

Important: the public corpus does NOT show IU repeatedly checking an ex-partner,
friend's SNS, game presence, online status, or similar private relationship
signals. IU evidence here is limited to public-reaction checking, self-search,
envy/comparison, and deliberate limits on monitoring. General checking-loop
ideas must be labelled as general behavioral perspectives, not IU biography.
"""

from backend import main_v46 as v46

core = v46.core

CHECKING_ALIASES = {
    "질투": ["envy", "jealousy", "comparison", "emotion", "relationships", "self-worth"],
    "질투나": ["envy", "jealousy", "comparison", "emotion", "relationships"],
    "부러": ["envy", "admiration", "comparison", "specificity", "self-context"],
    "염탐": ["checking", "monitoring", "rumination", "attention", "uncertainty", "relationships"],
    "몰래 봐": ["checking", "monitoring", "attention", "uncertainty", "relationships"],
    "몰래 확인": ["checking", "monitoring", "attention", "uncertainty", "relationships"],
    "sns": ["checking", "social-media", "attention", "comparison", "uncertainty"],
    "인스타": ["checking", "social-media", "comments", "attention", "comparison"],
    "스토리": ["checking", "social-media", "attention", "uncertainty", "relationships"],
    "프로필": ["checking", "monitoring", "attention", "uncertainty", "relationships"],
    "게임중": ["checking", "digital-status", "attention", "uncertainty", "relationships"],
    "게임 중": ["checking", "digital-status", "attention", "uncertainty", "relationships"],
    "게임하고 있": ["checking", "digital-status", "attention", "uncertainty", "relationships"],
    "접속중": ["checking", "digital-status", "attention", "uncertainty", "relationships"],
    "접속 중": ["checking", "digital-status", "attention", "uncertainty", "relationships"],
    "접속했": ["checking", "digital-status", "attention", "uncertainty", "relationships"],
    "온라인": ["checking", "digital-status", "attention", "uncertainty", "relationships"],
    "마지막 접속": ["checking", "digital-status", "attention", "uncertainty", "relationships"],
    "활동 상태": ["checking", "digital-status", "attention", "uncertainty", "relationships"],
    "상태 확인": ["checking", "digital-status", "monitoring", "attention", "uncertainty"],
    "계속 확인": ["checking", "reassurance-seeking", "rumination", "attention", "limits"],
    "자꾸 확인": ["checking", "reassurance-seeking", "rumination", "attention", "limits"],
    "또 확인": ["checking", "reassurance-seeking", "rumination", "attention", "limits"],
    "계속 검색": ["checking", "self-search", "monitoring", "attention", "rumination"],
    "자꾸 검색": ["checking", "self-search", "monitoring", "attention", "rumination"],
    "검색해 봐": ["checking", "monitoring", "attention", "uncertainty"],
    "찾아보게": ["checking", "monitoring", "attention", "uncertainty"],
    "차단했는데": ["checking", "boundaries", "monitoring", "attention", "rumination"],
    "차단해도": ["checking", "boundaries", "monitoring", "attention", "rumination"],
    "잘 지내나": ["checking", "uncertainty", "relationships", "comparison", "attention"],
    "나 없이": ["comparison", "loss", "relationships", "envy", "self-worth"],
    "누구 만나는": ["checking", "jealousy", "uncertainty", "relationships", "interpretation"],
    "새 사람": ["jealousy", "comparison", "loss", "relationships", "self-worth"],
    "반응 확인": ["reaction-monitoring", "checking", "social-feedback", "attention", "limits"],
    "댓글 확인": ["comments", "checking", "reassurance-seeking", "social-feedback", "attention"],
}

core.TOPIC_ALIASES.update(CHECKING_ALIASES)

CHECKING_QUERY_TRIGGERS = tuple(CHECKING_ALIASES.keys()) + (
    "확인하고 싶", "궁금해서 봤", "또 들어가", "계속 들어가", "계속 보게", "자꾸 보게",
    "뭐 하고 있나", "뭐하나", "누구랑", "비교하게", "신경 쓰여서 봐",
)

CHECKING_ENRICHMENT = (
    " checking reassurance-seeking monitoring reaction-monitoring self-search comments social-feedback"
    " attention limits letting-go rumination uncertainty digital-status social-media envy jealousy"
    " comparison specificity admiration self-context self-worth relationships boundaries focus"
    " self-regulation objectivity balance new-data interpretation"
)

_original_retrieve = core.retrieve_iu_evidence


def retrieve_iu_evidence_v47(message: str, context: dict | None, limit: int = 14):
    text = (message or "").lower()
    if any(trigger in text for trigger in CHECKING_QUERY_TRIGGERS):
        enriched = f"{message}\n[checking/comparison retrieval hints:{CHECKING_ENRICHMENT}]"
        return _original_retrieve(enriched, context, limit)
    return _original_retrieve(message, context, limit)


core.retrieve_iu_evidence = retrieve_iu_evidence_v47

core.IU_SYSTEM += """

질투·비교·확인욕구·디지털 상태 확인 관련 추가 원칙:
- 아이유가 연인·친구의 SNS, 게임 접속상태, 온라인 상태를 반복 확인했다는 공개 근거는 없다. 이런 행동을 아이유의 경험처럼 말하지 않는다.
- 이 축에서 아이유 자료는 외부 반응 확인, 자기검색, 부러움·비교, 반응 확인을 의도적으로 제한한 변화에만 직접 사용한다.
- 사용자가 상대 상태를 보고 싶어 하는 마음을 수치스럽거나 유치하다고 평가하지 않는다. 먼저 확인을 통해 무엇을 얻고 싶은지 묻는다: 사실, 안심, 연결감, 비교 우위, 분노 확인, 관계의 희망 등.
- 질투와 행동을 분리한다. 질투가 생겼다는 사실은 잘못이 아니지만, 그 감정을 반복 확인·공격·경계 침범으로 번역할 필요는 없다.
- '저 사람이 부럽다'를 사람 전체 비교로 두지 말고, 정확히 무엇이 부러운지 구체화한다. 구체적 욕구 정보와 '나는 열등하다'는 존재 판결을 분리한다.
- 디지털 상태는 디지털 상태일 뿐이다. 온라인, 게임중, 스토리 업로드, 팔로우 변화 같은 신호에서 상대의 숨은 감정·관계 의도·누구와 있는지를 사실처럼 추론하지 않는다.
- 반복 확인 문제에서는 '이번 확인이 정말 새 정보를 주는가?'를 본다. 새 정보가 없는데 같은 신호를 다시 확인하는 것은 정보 수집과 다른 기능을 할 수 있다.
- 확인행동이 잠깐의 안심 뒤 또 다른 확인 질문을 만드는 패턴은 일반적인 행동분석 관점으로 설명할 수 있지만, 아이유의 개인 경험으로 귀속하지 않는다.
- 확인을 줄이는 목표를 '더 이상 궁금하지 않게 되기'로만 두지 않는다. 궁금함이 남아 있어도 주의력을 다른 곳으로 돌리는 선택이 가능하다.
- 2021년 공개발언처럼 필요한 반응을 한 번 보고 이후 주의력을 회수하는 패턴은 확인 범위를 정하는 참고 근거로 사용할 수 있다.
- 사용자가 이미 차단·거리두기 경계를 세웠다면, 반복 확인이 그 경계를 사실상 우회하고 있는지 점검한다. 다만 사용자를 비난하지 않고 현재 필요한 마찰(friction)을 함께 찾는다.
- 일반 행동전략을 제안할 때는 아이유식 조언처럼 위장하지 않는다. 예: 확인 10분 미루기, 바로가기 제거, 확인 전 질문을 메모하기, 새 정보 여부 확인하기, 현재 행동 하나로 이동하기.
- 질투·확인욕구가 심각한 불안, 안전 문제, 강압적 감시, 타인의 계정 침입 등으로 이어지는 경우에는 사생활·안전·법적 경계를 우선한다.

질투·확인 질문에서는 가능하면 내부적으로 다음을 분리한다:
TRIGGER(촉발) / URGE(확인욕구) / NEED(얻고 싶은 감정·정보) / DIGITAL-FACT(실제 본 것) /
STORY(붙인 관계 해석) / NEW-DATA(다시 보면 새 정보가 생기는가) /
BOUNDARY(내 주의력을 어디까지 줄 것인가) / RETURN(내 삶으로 돌아오는 다음 행동).
"""

core.app.version = "4.7-iu-brain-checking"


def _health_v47():
    return {
        "ok": True,
        "service": "my-sea",
        "version": "4.7-iu-brain-checking",
        "iu_brain_observations": len(core.IU_BRAIN),
        "decision_arbitration": True,
        "decision_revision": True,
        "loss_reconnection": True,
        "anger_release": True,
        "checking_comparison": True,
    }


for route in core.app.routes:
    if getattr(route, "path", None) == "/health":
        route.endpoint = _health_v47
        if getattr(route, "dependant", None) is not None:
            route.dependant.call = _health_v47
        break

app = core.app
