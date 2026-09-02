"""IU Brain v4.5 — loneliness / loss / reconnection layer.

Builds on v4.4 decision revision. This layer improves retrieval and prompting
for relationship endings, loneliness, perceived rejection, loss, selective
trust, and gradual reconnection. It does not force reconciliation or infer
private motives from silence.
"""

from backend import main_v44 as v44

core = v44.core

LOSS_RECONNECTION_ALIASES = {
    "외로워": ["loneliness", "emotion", "connection", "focus", "belonging", "recovery"],
    "외롭": ["loneliness", "emotion", "connection", "focus", "belonging"],
    "혼자인 것 같": ["loneliness", "belonging", "connection", "emotion", "future"],
    "혼자 남": ["loneliness", "loss", "belonging", "connection", "future"],
    "소외": ["exclusion", "loneliness", "relationships", "belonging", "interpretation"],
    "따돌": ["exclusion", "relationships", "belonging", "safety", "support"],
    "읽씹": ["silence", "interpretation", "relationships", "uncertainty", "boundaries"],
    "답장이 없": ["silence", "interpretation", "relationships", "uncertainty"],
    "연락이 없": ["silence", "relationships", "uncertainty", "distance"],
    "연락 끊": ["closure", "distance", "relationships", "loss", "uncertainty"],
    "버림받": ["abandonment-feeling", "loss", "relationships", "self-worth", "interpretation"],
    "떠나갔": ["loss", "closure", "relationships", "grief", "future"],
    "떠났": ["loss", "closure", "relationships", "grief", "future"],
    "헤어졌": ["breakup", "loss", "closure", "grief", "relationships"],
    "이별": ["breakup", "loss", "closure", "grief", "relationships"],
    "관계가 끝": ["closure", "loss", "relationships", "past-relationship", "meaning"],
    "관계 끝": ["closure", "loss", "relationships", "past-relationship", "meaning"],
    "사람을 못 믿": ["trust", "selective-trust", "vulnerability", "relationships", "future"],
    "사람이 무서": ["trust", "self-protection", "vulnerability", "relationships", "future"],
    "또 상처": ["trust", "self-protection", "relationships", "future", "vulnerability"],
    "다시 믿": ["trust", "selective-trust", "reconnection", "relationships", "action"],
    "다시 사람": ["reconnection", "trust", "relationships", "future", "openness"],
    "마음을 열": ["vulnerability", "openness", "trust", "relationships", "boundaries"],
    "사람 관계가 무서": ["trust", "self-protection", "relationships", "future", "vulnerability"],
    "잊히지 않": ["loss", "grief", "rumination", "past-relationship", "meaning"],
    "계속 그 사람": ["loss", "rumination", "past-relationship", "closure", "emotion"],
    "좋았던 것도 거짓": ["past-relationship", "sincerity", "meaning", "closure", "interpretation"],
    "나를 싫어하": ["interpretation", "relationships", "evaluation", "uncertainty", "self-worth"],
}

core.TOPIC_ALIASES.update(LOSS_RECONNECTION_ALIASES)

LOSS_QUERY_TRIGGERS = tuple(LOSS_RECONNECTION_ALIASES.keys()) + (
    "상실", "그리워", "보고 싶", "관계", "친구가 떠", "사람 때문에",
)

LOSS_ENRICHMENT = (
    " loneliness loss breakup closure relationships trust selective-trust vulnerability openness"
    " reconnection belonging shared-purpose silence uncertainty interpretation self-worth"
    " past-relationship sincerity meaning boundaries grief future focus reality-check action"
)

_original_retrieve = core.retrieve_iu_evidence


def retrieve_iu_evidence_v45(message: str, context: dict | None, limit: int = 14):
    text = (message or "").lower()
    if any(trigger in text for trigger in LOSS_QUERY_TRIGGERS):
        enriched = f"{message}\n[loss and reconnection retrieval hints:{LOSS_ENRICHMENT}]"
        return _original_retrieve(enriched, context, limit)
    return _original_retrieve(message, context, limit)


core.retrieve_iu_evidence = retrieve_iu_evidence_v45

core.IU_SYSTEM += """

외로움·관계 종료·상실·다시 연결되기 관련 추가 원칙:
- 사용자가 '버림받았다'고 느낄 때 감정을 부정하지 않되, 실제 확인된 관계 행동과 '나는 버려질 사람이다'라는 자기 가치 해석을 분리한다.
- 무응답·읽씹·거리감만으로 상대의 숨은 의도나 감정을 확정하지 않는다. 한 번의 침묵인지 반복 패턴인지, 관계 수준과 맥락이 무엇인지 구분한다.
- 관계가 끝났다고 과거의 모든 좋은 순간과 진심까지 거짓이었다고 자동 재해석하지 않는다. 과거의 의미와 현재 부여할 신뢰·접근권은 별개의 질문이다.
- 반대로 과거에 진심이 있었다는 이유만으로 현재 다시 같은 신뢰나 친밀도를 회복해야 한다고 권하지 않는다. 현재의 반복 행동과 경계를 본다.
- 한 사람의 상처 주는 행동을 모든 사람의 미래 행동으로 일반화하지 않는다. 새로운 관계에는 새로운 행동 데이터가 쌓일 가능성을 남긴다.
- 다시 신뢰하기를 '전부 열기'로 정의하지 않는다. 작은 약속, 제한된 공유, 반복 행동을 통해 신뢰 범위를 단계적으로 업데이트할 수 있다.
- 타인의 진심 앞에서 연약해지는 것은 신뢰의 실패가 아닐 수 있지만, 취약함을 허용할 대상은 존중·일관성·경계 반응을 통해 선택한다.
- 외로움을 단순히 사람 수나 자극 부족으로만 해석하지 않는다. 연결, 집중, 안정, 애도, 휴식 중 무엇이 필요한 외로움인지 살핀다.
- 현재 혼자라는 감각을 미래의 영구 상태로 예언하지 않는다. 관계는 반복 접촉·공동 경험·작은 신뢰로 변할 수 있다.
- 관계 상실에는 애도의 시간이 필요할 수 있다. 다만 감정을 느끼는 것과 상대의 의도·과거 장면을 반복 확인하는 반추를 구분한다.
- 화해나 재접촉을 자동 목표로 두지 않는다. 안전·존중·반복 행동이 부족하면 거리 유지나 종료도 정당한 선택일 수 있다.
- 사별과 일반적인 관계 종료를 같은 사건으로 취급하지 않는다. 사별·중대한 상실에서는 상실의 현실과 애도 자체를 존중하고 성급한 '대체 관계'를 권하지 않는다.

관계 종료나 소외 질문에서는 가능하면 내부적으로 다음을 분리한다:
FACT(확인된 행동) / STORY(내가 붙인 해석) / GRIEF(잃은 것에 대한 감정) /
TRUST(현재 신뢰 수준) / BOUNDARY(허용할 거리) / NEXT-DATA(다음에 확인할 작은 행동).
"""

core.app.version = "4.5-iu-brain-reconnection"


def _health_v45():
    return {
        "ok": True,
        "service": "my-sea",
        "version": "4.5-iu-brain-reconnection",
        "iu_brain_observations": len(core.IU_BRAIN),
        "decision_arbitration": True,
        "decision_revision": True,
        "loss_reconnection": True,
    }


for route in core.app.routes:
    if getattr(route, "path", None) == "/health":
        route.endpoint = _health_v45
        if getattr(route, "dependant", None) is not None:
            route.dependant.call = _health_v45
        break

app = core.app
