"""IU Brain v5.0 — six-axis megabatch layer.

Builds on v4.9 uncertainty/control, preserving all earlier v4.x layers, then
adds bundled retrieval and reasoning support for:
- identity / authenticity / taste
- time / aging / past vs present
- collaboration / delegation / responsibility
- needs / gratitude / receiving recognition
- courage / challenge / comfort-zone expansion

Uncertainty / control / waiting remains provided by v4.9 and is integrated in
the synthesis rules below. The verified public-statement corpus remains the
source of evidence; this is not a literal model of IU's private mind.
"""

from backend import main_v49 as v49

core = v49.core

MEGA_ALIASES = {
    # 정체성 · 진정성 · 자기취향
    "내 취향": ["taste", "identity", "self-standard", "authenticity"],
    "내답게": ["identity", "authenticity", "self-standard", "freedom"],
    "나다운": ["identity", "authenticity", "self-standard", "comfort"],
    "진정성": ["authenticity", "self-honesty", "creativity", "identity"],
    "진심 아닌": ["authenticity", "self-honesty", "limits", "creativity"],
    "억지로": ["authenticity", "limits", "creativity", "pressure"],
    "가식": ["authenticity", "identity", "social-evaluation", "self-honesty"],
    "촌스럽": ["taste", "identity", "evaluation", "self-standard"],
    "남의 기준": ["evaluation", "taste", "identity", "self-standard"],

    # 시간 · 나이 · 과거와 현재
    "과거에": ["past", "time", "change", "reinterpretation"],
    "예전에는": ["past", "change", "time", "identity"],
    "나이 들": ["aging", "change", "time", "openness"],
    "30대": ["aging", "change", "freedom", "experience"],
    "시간이 지나": ["time", "change", "reinterpretation", "past"],
    "놓아야": ["letting-go", "past", "renewal", "time"],
    "붙잡고": ["letting-go", "past", "control", "attachment"],
    "졸업": ["letting-go", "past", "renewal", "time"],

    # 협업 · 위임 · 책임
    "협업": ["collaboration", "delegation", "trust", "responsibility"],
    "팀워크": ["collaboration", "teamwork", "responsibility", "trust"],
    "혼자 다": ["delegation", "collaboration", "responsibility", "limits"],
    "맡겨": ["delegation", "trust", "collaboration", "interpretation"],
    "위임": ["delegation", "trust", "responsibility", "collaboration"],
    "피드백": ["feedback", "collaboration", "trust", "clarification"],
    "의견을 듣": ["feedback", "listening", "collaboration", "humility"],
    "같이 일": ["collaboration", "teamwork", "mutual-development", "responsibility"],

    # 욕구 · 감사 · 인정받기
    "내가 원하는": ["needs", "desire", "specificity", "meaning"],
    "뭘 원하는": ["needs", "desire", "clarification", "meaning"],
    "채워지지": ["needs", "specificity", "meaning", "motivation"],
    "보상": ["needs", "reward", "motivation", "meaning"],
    "고마움": ["gratitude", "receiving", "relationships", "effort"],
    "감사": ["gratitude", "receiving", "relationships", "effort"],
    "인정받": ["recognition", "receiving", "social-evaluation", "self-worth"],
    "칭찬받": ["recognition", "receiving", "gratitude", "self-worth"],

    # 도전 · 용기 · 불편함 감수
    "도전": ["challenge", "courage", "experience", "uncertainty"],
    "새로운 경험": ["challenge", "experience", "curiosity", "aging"],
    "무섭지만": ["courage", "fear", "challenge", "action"],
    "불편하지만": ["challenge", "comfort-zone", "action", "values"],
    "익숙하지": ["challenge", "comfort-zone", "uncertainty", "experience"],
    "해볼까": ["experimentation", "challenge", "courage", "decision"],
    "해보고 싶": ["challenge", "experience", "agency", "courage"],
    "실패해도": ["challenge", "uncertainty", "experimentation", "recovery"],
}

core.TOPIC_ALIASES.update(MEGA_ALIASES)

MEGA_QUERY_TRIGGERS = tuple(MEGA_ALIASES.keys())
MEGA_ENRICHMENT = (
    " identity authenticity taste self-standard self-honesty interpretation audience-agency"
    " time aging past change openness reinterpretation letting-go renewal"
    " collaboration delegation trust responsibility feedback teamwork mutual-development tradeoff"
    " needs desire specificity meaning gratitude receiving recognition effort reward"
    " challenge courage experience curiosity comfort-zone experimentation action"
    " uncertainty control preparation flexibility waiting questions"
)

_original_retrieve = core.retrieve_iu_evidence


def retrieve_iu_evidence_v50(message: str, context: dict | None, limit: int = 14):
    text = (message or "").lower()
    if any(trigger in text for trigger in MEGA_QUERY_TRIGGERS):
        enriched = f"{message}\n[six-axis megabatch retrieval hints:{MEGA_ENRICHMENT}]"
        return _original_retrieve(enriched, context, limit)
    return _original_retrieve(message, context, limit)


core.retrieve_iu_evidence = retrieve_iu_evidence_v50

core.IU_SYSTEM += """

6축 메가배치 추가 판단 원칙:
- v4.9의 불확실성 원칙을 유지한다. 모르는 부분을 사실처럼 채우지 않고, 확인 가능한 사실·질문 가능한 정보·통제 가능한 준비·통제 불가능한 결과를 나눈다.
- 준비를 많이 했다는 이유로 준비한 계획을 현실보다 우선하지 않는다. 현실이 달라지면 준비를 수정하거나 놓을 수 있다.
- 타인의 취향·평가가 존재하는 것과 자신의 취향·기준을 버려야 하는 것을 동일시하지 않는다. 다른 사람이 싫어할 수 있어도 자신은 좋아할 수 있다.
- 진정성을 모든 사실의 고백이나 자전적 표현과 동일시하지 않는다. 상상·역할·창작을 사용하더라도 자신의 기준과 책임에 충실할 수 있다.
- 할 말이 없거나 진심이 아닌 상태에서 억지 산출을 계속하는 것을 항상 성실함으로 보지 않는다. 기다림·수정·중단이 더 책임 있는 선택일 수 있다.
- 과거의 자기정의와 현재의 자기정의를 다르게 가질 수 있다. 과거를 부정하지 않고도 현재의 중심에서 내려놓을 수 있다.
- 오래된 선택·취향·관계·대표작을 계속 유지하는 것만이 충성이나 일관성은 아니다. 새로운 경험이 생기면 현재에 맞게 비중을 바꿀 수 있다.
- 협업에서 책임감이 높다고 모든 권한을 독점하지 않는다. 상대의 전문성·해석·아이디어가 들어올 공간을 만들고, 자신이 최종 책임질 범위를 구분한다.
- '혼자 해야 마음이 놓인다'는 상태가 실제 품질을 높이는지, 불확실성을 줄이기 위한 통제 행동인지 구분한다.
- 사용자의 욕구를 다른 종류의 보상으로 섣불리 덮지 않는다. 돈·인정·친밀함·휴식·자유·성취·새로운 경험 중 무엇이 실제로 필요한지 구체화한다.
- 큰 인정이나 칭찬을 받을 때 어색함과 기쁨이 동시에 존재할 수 있다. 어색하다는 이유로 인정을 부정하거나, 인정받았다는 이유로 그 수식어를 자기 존재 전체와 동일시하지 않는다.
- 불편함과 위험을 구분한다. 익숙하지 않거나 민망한 것은 실제 안전·법적·재정적 위험과 다르며, 되돌릴 수 있는 도전에서는 불편함을 감수할 가치가 있을 수 있다.
- 반대로 모든 불편함을 성장통으로 미화하지 않는다. 현재 자원·회복 가능성·핵심 가치·가역성을 함께 본다.
- 나이가 들었다는 이유만으로 새로운 경험 가능성을 줄이지 않는다. 현재 감각과 호기심을 유지하기 위해 의도적으로 새 경험을 선택할 수 있다.

복합 질문에서는 가능하면 다음 순서를 내부적으로 사용한다:
FACT(확실히 아는 것) / UNKNOWN(모르는 것) / NEED(진짜 원하는 것) / SELF(내 기준·취향) /
TIME(과거와 지금의 변화) / CONTROL(통제 가능한 것) / DELEGATE(혼자 쥐지 않아도 되는 것) /
RISK(실제 위험과 불편함) / EXPERIENCE(결과 외 얻는 경험) / NEXT(작은 다음 행동).
"""

core.app.version = "5.3-ai-connect"


def _health_v50():
    return {
        "ok": True,
        "service": "my-sea",
        "version": "5.3-ai-connect",
        "iu_brain_observations": len(core.IU_BRAIN),
        "principle_situations": len(core.PRINCIPLE_SITUATIONS),
        "decision_arbitration": True,
        "decision_revision": True,
        "loss_reconnection": True,
        "anger_release": True,
        "checking_comparison": True,
        "shame_rejection": True,
        "uncertainty_control": True,
        "six_axis_megabatch": True,
    }


for route in core.app.routes:
    if getattr(route, "path", None) == "/health":
        route.endpoint = _health_v50
        if getattr(route, "dependant", None) is not None:
            route.dependant.call = _health_v50
        break

app = core.app
