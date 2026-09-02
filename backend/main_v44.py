"""IU Brain v4.4 — decision revision / regret handling layer.

Builds on v4.3 arbitration. This layer strengthens retrieval and prompting for
choices, regret, pausing, revising plans, and learning after outcomes. It does
not make decisions for the user or claim IU would choose one fixed answer.
"""

from backend import main_v43 as v43

core = v43.core

DECISION_ALIASES = {
    "후회": ["regret", "decision", "learning", "revision", "reflection"],
    "선택": ["decision", "agency", "values", "tradeoff", "uncertainty"],
    "결정": ["decision", "agency", "responsibility", "uncertainty", "revision"],
    "잘못 선택": ["regret", "decision", "revision", "learning", "self-criticism"],
    "잘못 결정": ["regret", "decision", "revision", "learning", "self-criticism"],
    "실수": ["mistake", "learning", "responsibility", "completion", "iteration"],
    "다시 결정": ["revision", "decision", "new-evidence", "agency", "time"],
    "바꿔도": ["revision", "decision", "flexibility", "new-evidence", "agency"],
    "마음이 바뀌": ["revision", "change", "decision", "time", "reinterpretation"],
    "계속할까": ["decision", "persistence", "sustainability", "limits", "meaning"],
    "그만둘까": ["decision", "close", "limits", "meaning", "recovery"],
    "포기": ["close", "pause", "persistence", "limits", "decision"],
    "보류": ["pause", "decision", "reversibility", "uncertainty"],
    "잠시 멈": ["pause", "decision", "reversibility", "recovery"],
    "미룰까": ["pause", "decision", "responsibility", "reversibility"],
    "돌이킬": ["reversibility", "decision", "regret", "time"],
    "되돌릴": ["reversibility", "decision", "revision", "uncertainty"],
    "매몰비용": ["sunk-cost", "revision", "decision", "new-evidence"],
    "이미 많이": ["sunk-cost", "revision", "decision", "effort"],
    "여기까지 했": ["sunk-cost", "revision", "decision", "effort"],
    "새로운 정보": ["new-evidence", "revision", "decision", "learning"],
    "생각이 바뀌": ["revision", "reinterpretation", "decision", "time"],
    "책임져야": ["responsibility", "decision", "limits", "accountability"],
    "내가 선택": ["agency", "decision", "responsibility", "regret"],
}

core.TOPIC_ALIASES.update(DECISION_ALIASES)

DECISION_QUERY_TRIGGERS = tuple(DECISION_ALIASES.keys()) + (
    "어떻게 해야", "뭘 해야", "어느 쪽", "해야 할까", "해도 될까",
)

DECISION_ENRICHMENT = (
    " decision regret revision new-evidence sunk-cost agency responsibility uncertainty"
    " reversibility pause close persistence experimentation values tradeoff control effort"
    " learning iteration completion flexibility time reinterpretation limits resources"
)

_original_retrieve = core.retrieve_iu_evidence


def retrieve_iu_evidence_v44(message: str, context: dict | None, limit: int = 14):
    text = (message or "").lower()
    if any(trigger in text for trigger in DECISION_QUERY_TRIGGERS):
        enriched = f"{message}\n[decision revision retrieval hints:{DECISION_ENRICHMENT}]"
        return _original_retrieve(enriched, context, limit)
    return _original_retrieve(message, context, limit)


core.retrieve_iu_evidence = retrieve_iu_evidence_v44

core.IU_SYSTEM += """

의사결정·후회·수정 관련 추가 원칙:
- 사용자를 대신해 중요한 결정을 확정하지 않는다. 공개자료에서 드러나는 판단 패턴과 사용자의 현실 조건을 비교해 선택지를 정리한다.
- 결정 전에 '정답인가'만 묻지 말고 가역성, 행동하지 않았을 때의 비용, 현재 자원, 통제 가능한 변수, 핵심 가치를 함께 본다.
- 되돌릴 수 있는 결정은 필요한 경우 작은 실험(EXPERIMENT)으로 정보부터 얻는 선택을 고려한다.
- 이미 시간·노력·돈을 많이 썼다는 이유만으로 계속해야 한다고 판단하지 않는다. 이후 들어온 새로운 정보가 이전 가정을 깨뜨렸는지 본다.
- 반대로 새 정보 없이 불안만 커졌다는 이유로 계획을 계속 갈아엎도록 권하지 않는다.
- '잠시 멈춤(PAUSE)'과 '수정(REVISE)'과 '종료(CLOSE)'를 서로 다른 선택으로 취급한다. 지금 멈추는 것을 영원한 포기로 확대하지 않는다.
- 책임은 원래 계획을 끝까지 고집하는 것만을 뜻하지 않는다. 현재 자원과 약속 사이에 불일치가 생기면 설명·조정·재계획도 책임 있는 행동일 수 있다.
- 선택 후 아쉬움이나 후회가 생겼다는 사실만으로 그 선택이 당시에도 틀렸다고 단정하지 않는다. 당시 알 수 있었던 정보와 지금 새로 알게 된 정보를 분리한다.
- 후회가 실제로 무시했던 위험 신호를 가리키는지, 결과가 마음에 들지 않는 슬픔인지, 지금 가치관이 변해 생긴 재평가인지 구분한다.
- 완료한 결과에 아쉬움이 남아도 그것을 다음 반복의 피드백으로 사용할 수 있다. 완성과 아쉬움은 동시에 존재할 수 있다.
- 과거의 자신에게 '그때의 정보로는 그 선택이 이해된다'고 말하면서도 현재에는 다른 결정을 할 수 있다. 이는 자기모순이 아니라 정보와 가치의 업데이트일 수 있다.
- A와 B가 실제로 상호보완적인 선택지라면 하나를 완전히 제거하지 않고 비중·시간·역할을 나누는 포트폴리오 선택도 검토한다.

결정 질문에서는 가능하면 다음 다섯 상태를 내부적으로 구분한다:
PROCEED(계속) / EXPERIMENT(작게 시험) / PAUSE(잠시 멈춤) / REVISE(수정) / CLOSE(종료).
답변에서 상태명을 기계적으로 나열할 필요는 없지만, 왜 그 방향이 현재 정보에 맞는지 설명한다.
"""

core.app.version = "4.4-iu-brain-decisions"


def _health_v44():
    return {
        "ok": True,
        "service": "my-sea",
        "version": "4.4-iu-brain-decisions",
        "iu_brain_observations": len(core.IU_BRAIN),
        "decision_arbitration": True,
        "decision_revision": True,
    }


for route in core.app.routes:
    if getattr(route, "path", None) == "/health":
        route.endpoint = _health_v44
        if getattr(route, "dependant", None) is not None:
            route.dependant.call = _health_v44
        break

app = core.app
