"""IU Brain v4.6 — anger / demonization / accountability / release layer.

Builds on v4.5 reconnection. This layer improves retrieval and prompting for
anger, resentment, demonization, accountability, criticism, forgiveness
questions, and releasing attention after a hurtful relationship.

Important: the public-statement corpus does NOT currently support attributing a
complete 'forgiveness doctrine' to IU. Forgiveness-specific guidance is
therefore explicitly framed as a research synthesis of adjacent supported
patterns, not as a direct IU teaching.
"""

from backend import main_v45 as v45

core = v45.core

ANGER_ALIASES = {
    "화나": ["anger", "violation", "emotion", "boundaries", "accountability"],
    "화가 나": ["anger", "violation", "emotion", "boundaries", "accountability"],
    "분노": ["anger", "violation", "emotion", "accountability", "rumination"],
    "빡쳐": ["anger", "violation", "emotion", "boundaries"],
    "열받": ["anger", "violation", "emotion", "boundaries"],
    "원망": ["resentment", "anger", "loss", "rumination", "release"],
    "억울": ["injustice", "anger", "accountability", "interpretation", "validation"],
    "괘씸": ["anger", "judgment", "accountability", "relationships"],
    "악마화": ["demonization", "judgment", "complexity", "interpretation", "anger"],
    "나쁜 사람": ["judgment", "demonization", "complexity", "behavior", "interpretation"],
    "악한 사람": ["judgment", "demonization", "complexity", "personhood"],
    "복수": ["revenge", "anger", "rumination", "release", "accountability"],
    "되갚": ["revenge", "anger", "reciprocity", "release"],
    "벌 받": ["justice", "anger", "accountability", "release"],
    "사과받": ["apology", "repair", "accountability", "validation", "relationships"],
    "사과해야": ["apology", "impact", "responsibility", "repair"],
    "용서": ["forgiveness", "release", "boundaries", "trust", "reconciliation"],
    "화해": ["reconciliation", "trust", "boundaries", "relationships", "repair"],
    "정의": ["justice", "accountability", "values", "judgment"],
    "잘못 인정": ["accountability", "apology", "validation", "repair"],
    "혐오": ["hate", "anger", "boundaries", "personhood", "restraint"],
    "증오": ["hate", "anger", "resentment", "release"],
    "미워": ["hate", "anger", "ambivalence", "relationships", "release"],
    "싫어 죽겠": ["hate", "anger", "resentment", "release"],
    "내려놓": ["release", "letting-go", "rumination", "attention", "boundaries"],
    "잊고 싶": ["release", "letting-go", "loss", "rumination", "recovery"],
    "계속 확인": ["rumination", "checking", "anger", "loss", "release"],
    "잘 사나": ["checking", "rumination", "resentment", "release"],
    "내가 틀렸": ["reality-check", "feedback", "judgment", "uncertainty"],
}

core.TOPIC_ALIASES.update(ANGER_ALIASES)

ANGER_QUERY_TRIGGERS = tuple(ANGER_ALIASES.keys()) + (
    "화났", "미움", "복수하고 싶", "용서해야", "정의롭", "불공정", "상대가 잘못",
)

ANGER_ENRICHMENT = (
    " anger resentment hate demonization judgment complexity interpretation behavior personhood"
    " criticism feedback malice boundaries accountability apology impact repair justice release"
    " letting-go rumination checking trust reconciliation forgiveness restraint kindness values"
    " reality-check attention self-protection relationships"
)

_original_retrieve = core.retrieve_iu_evidence


def retrieve_iu_evidence_v46(message: str, context: dict | None, limit: int = 14):
    text = (message or "").lower()
    if any(trigger in text for trigger in ANGER_QUERY_TRIGGERS):
        enriched = f"{message}\n[anger/accountability/release retrieval hints:{ANGER_ENRICHMENT}]"
        return _original_retrieve(enriched, context, limit)
    return _original_retrieve(message, context, limit)


core.retrieve_iu_evidence = retrieve_iu_evidence_v46

core.IU_SYSTEM += """

분노·악마화·책임·미움을 내려놓기 관련 추가 원칙:
- 분노를 나쁜 감정으로 취급해 즉시 없애려 하지 않는다. 분노가 어떤 경계 침범·배신·불공정·상실을 가리키는지 먼저 본다.
- '저 행동은 잘못됐다'와 '저 사람은 본질적으로 악하다'를 분리한다. 행동을 정확히 평가하면서도 상대의 숨은 의도·인격 전체를 사실처럼 확정하지 않는다.
- 사람을 입체적으로 보는 것은 잘못을 미화하거나 책임을 면제하는 일이 아니다. 반복 행동, 책임 인정, 경계 반응, 신뢰 근거를 구체적으로 본다.
- 비판·취향·오해·명백한 악의를 같은 범주로 뭉뚱그리지 않는다. 공개자료에서 명백한 악의는 피드백과 단호하게 분리해야 한다는 관점이 확인된다.
- 사용자가 영향력이나 확신을 가진 상황에서는 반대 의견을 들을 필요가 있는지, 자신의 판단 환경이 왜곡되지 않았는지 현실검증을 고려한다.
- 자신의 의도와 해석의 자유를 지키는 것과, 상대에게 실제로 발생한 상처·영향을 인정하고 책임지는 것은 동시에 가능하다.
- 책임을 묻는 것과 사람 전체를 비인간화하는 것을 동일시하지 않는다. 필요한 사과·수정·거리두기·차단은 구체적 행동 수준에서 다룬다.
- 현재 코퍼스에는 아이유가 '용서'를 체계적으로 정의한 충분한 직접 공개자료가 없다. 따라서 용서 질문에서는 '아이유는 용서를 이렇게 정의한다'고 말하지 않는다.
- 용서 질문은 연구용 일반 구분으로 이해/허용/용서/화해/신뢰회복을 서로 분리한다. 이 구분은 아이유의 직접 인용이 아니라 코퍼스 주변 근거를 안전하게 적용하기 위한 합성 규칙이라고 명시할 수 있다.
- 내려놓기를 '그 일이 괜찮았다고 인정하기'나 '다시 관계 맺기'로 정의하지 않는다. 상처 기억과 경계는 유지하면서도 반복 추론·확인·상대의 인정에 대한 집착에서 주의력을 회수할 수 있다.
- '사랑이 미움을 이긴다'는 공개 가치관은 해로운 행동을 허용하라는 뜻으로 쓰지 않는다. 사랑은 내가 어떤 방향의 사람이 될지에 관한 가치이고, 경계는 상대에게 어떤 접근권을 줄지에 관한 현실 규칙일 수 있다.
- 악마화가 올라오는 상황에서는 가능하면 FACT(행동) / VIOLATION(침해) / ANGER(감정) / STORY(사람 전체 판결) / BOUNDARY(경계) / ACCOUNTABILITY(책임) / RELEASE(주의력 회수)를 구분한다.
- 분노가 강한 상태에서 복수·보복·파괴적 행동을 부추기지 않는다. 안전과 현실적 결과를 우선하고, 필요한 경우 거리두기·기록·공식적 해결 절차·지지 요청 같은 비폭력적 선택을 우선한다.
"""

core.app.version = "4.6-iu-brain-anger-release"


def _health_v46():
    return {
        "ok": True,
        "service": "my-sea",
        "version": "4.6-iu-brain-anger-release",
        "iu_brain_observations": len(core.IU_BRAIN),
        "decision_arbitration": True,
        "decision_revision": True,
        "loss_reconnection": True,
        "anger_release": True,
    }


for route in core.app.routes:
    if getattr(route, "path", None) == "/health":
        route.endpoint = _health_v46
        if getattr(route, "dependant", None) is not None:
            route.dependant.call = _health_v46
        break

app = core.app
