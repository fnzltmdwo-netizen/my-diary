"""IU Brain v4.2 — work / effort / rest / sustainability extension.

This module intentionally imports the stable v4.1 server and applies a narrow
retrieval/prompt extension. Keeping the base server untouched makes it easy to
roll back while the corpus keeps growing.
"""

from backend import main as base


WORK_ALIASES = {
    "과로": ["work", "depletion", "burnout", "limits", "sustainability", "self-care"],
    "워커홀릭": ["work", "overinvestment", "balance", "sustainability", "self-observation"],
    "일밖에": ["work", "identity", "overinvestment", "balance", "meaning"],
    "일만": ["work", "identity", "overinvestment", "balance", "meaning"],
    "일 때문에": ["work", "pressure", "depletion", "limits", "meaning"],
    "일이 너무": ["work", "pressure", "depletion", "limits", "sustainability"],
    "일을 너무": ["work", "pressure", "depletion", "limits", "sustainability"],
    "쉬면 불안": ["rest", "anxiety", "work", "balance", "self-care"],
    "쉬면 죄책감": ["rest", "guilt", "work", "self-compassion", "limits"],
    "쉬는 게": ["rest", "self-care", "limits", "sustainability"],
    "연습": ["practice", "learning", "work", "intrinsic-motivation", "growth"],
    "노력": ["effort", "practice", "process", "work", "sustainability"],
    "의욕": ["motivation", "activation", "work", "recovery"],
    "고갈": ["depletion", "burnout", "creativity", "rest", "limits"],
    "창작이 안": ["burnout", "depletion", "creativity", "limits", "authenticity"],
    "일이 안": ["work", "motivation", "activation", "limits"],
    "일을 그만두고 싶": ["work", "burnout", "limits", "meaning", "recovery", "decision"],
    "오래 하고 싶": ["sustainability", "work", "self-care", "meaning", "limits"],
    "버티": ["persistence", "sustainability", "limits", "self-care", "recovery"],
    "업무": ["work", "effort", "pressure", "responsibility", "limits"],
    "직장": ["work", "pressure", "meaning", "limits", "sustainability"],
    "회사": ["work", "pressure", "meaning", "responsibility", "limits"],
    "퇴사": ["work", "meaning", "limits", "decision", "recovery"],
    "커리어": ["work", "career", "meaning", "growth", "sustainability"],
    "직업": ["work", "career", "meaning", "identity", "sustainability"],
}

base.TOPIC_ALIASES.update(WORK_ALIASES)

WORK_QUERY_TRIGGERS = tuple(WORK_ALIASES.keys()) + (
    "번아웃", "소진", "지쳤", "지쳐", "휴식", "고생", "성과 압박", "마감",
)

WORK_ENRICHMENT = (
    " work effort practice learning intrinsic-motivation rest recovery depletion burnout"
    " sustainability limits self-care meaning responsibility collaboration energy balance"
    " overinvestment creativity authenticity process"
)

_original_retrieve = base.retrieve_iu_evidence


def retrieve_iu_evidence_v42(message: str, context: dict | None, limit: int = 14):
    text = (message or "").lower()
    if any(trigger in text for trigger in WORK_QUERY_TRIGGERS):
        # Retrieval-only enrichment. The user-visible prompt still receives the
        # original message, not these hidden topic hints.
        return _original_retrieve((message or "") + WORK_ENRICHMENT, context, limit)
    return _original_retrieve(message, context, limit)


base.retrieve_iu_evidence = retrieve_iu_evidence_v42

base.IU_SYSTEM += """

일·노력·휴식·번아웃 관련 추가 원칙:
- 생산성이 높다는 이유만으로 건강한 상태라고 판단하지 않는다. 공개 자료에서도 큰 성취와 공허·소진이 동시에 나타날 수 있다.
- 일을 좋아하고 일에서 생각이 정리되는 성향과, 일을 감정을 피하는 수단으로 사용하는 것은 구분한다.
- 휴식을 무조건 아무것도 하지 않는 상태로만 보지 않는다. 리듬·역할·활동 방식의 변화가 회복으로 작동한 공개 사례도 있다.
- 번아웃·고갈·의욕 저하를 도덕적 실패나 게으름으로 단정하지 않는다. 현재 자원과 한계, 의미, 회복 필요를 함께 본다.
- 노력은 양만 보지 않는다. 즐거움·학습 방식·경험의 폭·협업·과정 보상도 노력의 질을 구성할 수 있다.
- 자기 기준과 책임감은 강한 동력이 될 수 있지만, 그 기준이 자기 존재 가치의 판결이나 자기소진으로 넘어가는지 별도로 확인한다.
- '더 버텨라'와 '무조건 그만둬라' 중 하나를 자동 선택하지 않는다. 사용자가 오래 지속하고 싶은 것인지, 현재 한계를 넘긴 것인지, 의미가 사라진 것인지 구분한다.
- 아이유가 바쁜 일정이나 불편한 상태에서도 일을 이어간 공개 사례를 사용자의 과로·통증·질병을 참고 견디라는 근거로 사용하지 않는다.
- 지속가능성은 단순히 오래 일하는 것이 아니라, 건강·관계·감정·의미를 보존하면서 중요한 일을 이어갈 수 있는지를 포함한다.
"""

base.app.version = "4.2-iu-brain-work"
app = base.app
