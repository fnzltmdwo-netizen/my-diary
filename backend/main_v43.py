"""IU Brain v4.3 — cross-axis decision arbitration layer.

Imports the stable v4.2 server and adds a narrow layer that deliberately
retrieves evidence from both sides of common value conflicts. The purpose is
not to pretend IU has one universal rule, but to compare multiple public-
statement patterns before advice is generated.
"""

from backend import main_v42 as v42

core = v42.base


ARBITRATION_PROFILES = {
    "love_boundary": {
        "triggers": ("사랑", "미워", "용서", "경계", "신뢰", "떠났", "관계", "참아", "선 넘"),
        "topics": (
            "love care companionship relationships boundaries trust respect self-protection "
            "nonpossessive-love reciprocity ambivalence action"
        ),
    },
    "acceptance_growth": {
        "triggers": ("자기수용", "자책", "자기비난", "부족", "완벽", "엄격", "성장", "바꾸고 싶", "나아지고 싶"),
        "topics": (
            "self-acceptance self-love self-compassion self-criticism growth standards "
            "imperfection agency completion self-evaluation"
        ),
    },
    "work_rest": {
        "triggers": ("일", "업무", "직장", "회사", "퇴사", "노력", "번아웃", "과로", "휴식", "쉬", "지쳐", "고갈"),
        "topics": (
            "work effort practice motivation rest recovery sustainability limits meaning "
            "overinvestment depletion burnout self-care process"
        ),
    },
    "emotion_action": {
        "triggers": ("감정", "불안", "걱정", "슬프", "공허", "허전", "반추", "계속 생각", "억누", "회복", "매몰"),
        "topics": (
            "emotion acceptance rumination recovery problem-solving action time cycles "
            "self-observation letting-go persistence"
        ),
    },
    "evaluation_self": {
        "triggers": ("평가", "악플", "인정", "비교", "남들은", "남보다", "성과", "실패", "성공", "실망", "순위", "1등"),
        "topics": (
            "evaluation feedback self-standard self-worth attribution comparison process "
            "success failure recognition scope selective-attention"
        ),
    },
    "confidence_fear": {
        "triggers": ("자신감", "두려", "무서", "실망시킬", "기대", "부담"),
        "topics": (
            "confidence fear love expectations responsibility balance uncertainty self-protection"
        ),
    },
    "control_flexibility": {
        "triggers": ("계획", "통제", "예상", "불확실", "모르겠", "미래", "선택", "결정", "후회"),
        "topics": (
            "planning preparation control uncertainty flexibility agency decision future "
            "acceptance effort"
        ),
    },
}


_original_retrieve = core.retrieve_iu_evidence


def _matched_profiles(message: str) -> list[str]:
    text = (message or "").lower()
    matched = []
    for name, profile in ARBITRATION_PROFILES.items():
        if any(trigger in text for trigger in profile["triggers"]):
            matched.append(name)
    return matched


def retrieve_iu_evidence_v43(message: str, context: dict | None, limit: int = 14):
    matched = _matched_profiles(message)
    if not matched:
        return _original_retrieve(message, context, limit)

    # Inject retrieval-only counterbalance hints so the evidence pack contains
    # both poles of a conflict when the corpus supports them. The model still
    # receives the user's original message in the visible advice prompt.
    hints = " ".join(ARBITRATION_PROFILES[name]["topics"] for name in matched)
    enriched = f"{message}\n[retrieval conflict balance: {hints}]"
    return _original_retrieve(enriched, context, limit)


core.retrieve_iu_evidence = retrieve_iu_evidence_v43

core.IU_SYSTEM += """

교차축 판단 추가 원칙 (연구 합성 규칙):
- 사용자의 고민에 서로 충돌하는 두 가치가 있으면 한쪽을 성급히 제거하지 말고, 각각을 지지하는 IU Brain 근거를 먼저 비교한다.
- '사랑 vs 경계'에서는 사랑의 존재와 현재 부여할 신뢰·접근권을 분리한다. 사랑이 있다고 무제한 허용을 뜻하지 않고, 경계를 세웠다고 과거의 좋은 감정이 거짓이었다고 단정하지 않는다.
- '자기수용 vs 성장'에서는 자신을 사랑할 조건과 개선하고 싶은 영역을 분리한다. 변화의 동기가 자기혐오인지 자기 기준에 따른 선택인지 살핀다.
- '노력 vs 휴식'에서는 중요한 일을 계속하고 싶은지와 현재 방식이 지속 가능한지를 별개의 질문으로 둔다. 더 버티는 것 자체를 성실함의 증거로 취급하지 않는다.
- '감정 수용 vs 행동 복귀'에서는 감정을 충분히 느끼는 것과 같은 해석을 반복 재생하는 반추를 구분한다. 감정을 인정한 뒤 현재로 돌아오는 행동도 허용한다.
- '타인의 평가 vs 자기 기준'에서는 평가자를, 평가 대상을, 근거의 질을 구분한다. 피드백은 정보로 사용하되 자기 존재 가치의 총점으로 사용하지 않는다.
- 자신감과 두려움처럼 반대 감정이 동시에 존재할 수 있다. 한쪽이 있다고 다른 쪽을 가짜로 판단하지 않는다.
- 준비와 유연함을 반대말로 취급하지 않는다. 충분히 준비한 뒤 현실이 달라지면 준비를 놓을 수 있는 유연성도 선택지다.
- 자료가 양쪽으로 갈리면 '아이유라면 반드시 이렇게 한다'고 단정하지 말고, 공개자료가 보여주는 긴장과 사용자가 선택할 수 있는 현실적 관점을 제시한다.
- 조언의 최종 선택은 사용자의 실제 상황·반복 행동·현재 자원·경계를 우선 확인한 뒤 제안한다.
"""

core.app.version = "4.3-iu-brain-arbitration"

# Keep /health truthful even though the base route was originally created in
# v4.1. Updating both endpoint and dependant call before serving requests makes
# the reported version/count reflect the active wrapper.
def _health_v43():
    return {
        "ok": True,
        "service": "my-sea",
        "version": "4.3-iu-brain-arbitration",
        "iu_brain_observations": len(core.IU_BRAIN),
        "decision_arbitration": True,
    }

for route in core.app.routes:
    if getattr(route, "path", None) == "/health":
        route.endpoint = _health_v43
        if getattr(route, "dependant", None) is not None:
            route.dependant.call = _health_v43
        break

app = core.app
