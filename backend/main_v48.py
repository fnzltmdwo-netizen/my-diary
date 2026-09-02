"""IU Brain v4.8 — shame / rejection / dignity layer.

Builds on v4.7 checking-comparison. This layer improves retrieval and prompting
for embarrassment, shame-like self-judgment, rejection, humiliation, pride,
approval seeking, and psychological safety.

Important: the public corpus does not support diagnosing IU with rejection
sensitivity or a clinical shame construct. Evidence is limited to public
remarks about embarrassment, social evaluation, approval, receiving love,
performance exposure, and trusted relationships.
"""

from backend import main_v47 as v47

core = v47.core

SHAME_ALIASES = {
    "창피": ["shame", "embarrassment", "social-evaluation", "exposure", "self-standard"],
    "민망": ["embarrassment", "social-evaluation", "exposure", "rejection"],
    "쪽팔": ["shame", "embarrassment", "social-evaluation", "dignity"],
    "수치": ["shame", "embarrassment", "self-worth", "social-evaluation"],
    "부끄": ["shame", "embarrassment", "receiving-love", "social-evaluation"],
    "초라": ["shame", "self-worth", "comparison", "social-evaluation", "rejection"],
    "거절당": ["rejection", "social-evaluation", "self-worth", "relationships", "emotion"],
    "무시당": ["rejection", "social-evaluation", "dignity", "relationships"],
    "무시받": ["rejection", "social-evaluation", "dignity", "relationships"],
    "체면": ["face", "social-evaluation", "pride", "dignity", "embarrassment"],
    "자존심 상": ["pride", "social-evaluation", "self-standard", "dignity", "emotion"],
    "자존심": ["pride", "self-standard", "dignity", "comparison"],
    "인정받고 싶": ["recognition", "approval", "social-evaluation", "effort", "self-worth"],
    "인정 못 받": ["recognition", "rejection", "social-evaluation", "self-worth"],
    "평가받는": ["evaluation", "social-evaluation", "shame", "self-standard"],
    "사람들이 볼까": ["social-evaluation", "exposure", "shame", "embarrassment"],
    "남들이 볼까": ["social-evaluation", "exposure", "shame", "embarrassment"],
    "실수 들": ["mistake", "shame", "embarrassment", "repair", "learning"],
    "들켰": ["exposure", "shame", "embarrassment", "social-evaluation"],
    "모른다고 말": ["help-seeking", "shame", "psychological-safety", "learning"],
    "도움 요청": ["help-seeking", "psychological-safety", "shame", "feedback", "learning"],
    "질문하기 창피": ["help-seeking", "psychological-safety", "shame", "learning"],
    "나를 싫어하": ["rejection", "interpretation", "social-evaluation", "self-worth", "relationships"],
    "싫어할까": ["rejection", "social-evaluation", "approval", "relationships", "uncertainty"],
    "호감 잃": ["rejection", "approval", "relationships", "social-evaluation"],
}

core.TOPIC_ALIASES.update(SHAME_ALIASES)

SHAME_QUERY_TRIGGERS = tuple(SHAME_ALIASES.keys()) + (
    "창피해서", "민망해서", "부끄러워서", "초라해 보여", "내가 한심", "내가 별로",
    "거절이 무서", "망신", "체면 구", "사람들 앞에서", "평가대", "인정 욕구",
)

SHAME_ENRICHMENT = (
    " shame embarrassment rejection social-evaluation exposure approval recognition pride face"
    " dignity self-worth self-standard imperfection psychological-safety help-seeking feedback"
    " receiving-love receptivity performance persistence repair learning interpretation scope"
    " play freedom regret relationships trust"
)

_original_retrieve = core.retrieve_iu_evidence


def retrieve_iu_evidence_v48(message: str, context: dict | None, limit: int = 14):
    text = (message or "").lower()
    if any(trigger in text for trigger in SHAME_QUERY_TRIGGERS):
        enriched = f"{message}\n[shame/rejection retrieval hints:{SHAME_ENRICHMENT}]"
        return _original_retrieve(enriched, context, limit)
    return _original_retrieve(message, context, limit)


core.retrieve_iu_evidence = retrieve_iu_evidence_v48

core.IU_SYSTEM += """

수치심·창피함·거절·체면·존엄 관련 추가 원칙:
- 아이유에게 임상적 거절민감성이나 수치심 장애가 있다고 진단하거나 암시하지 않는다. 공개발언의 창피함·민망함·평가 경험만 근거로 사용한다.
- '실제 잘못이 있다'와 '내 존재 자체가 잘못됐다'를 분리한다. 필요한 경우 행동을 수정·사과할 수 있지만 자기 존재 전체를 유죄로 만들지 않는다.
- 거절·무관심·낮은 평가가 실제로 아플 수 있다는 점은 인정하되, 한 사람·한 무대·한 결과를 자기 가치의 총점으로 확대하지 않는다.
- 창피함을 자동으로 위험 신호로 취급하지 않는다. 실제 안전·법적·재정적 위험과 되돌릴 수 있는 사회적 민망함을 구분한다.
- 체면을 지키는 것과 존엄을 지키는 것을 분리한다. 모른다고 말하기, 질문하기, 먼저 사과하기, 도움을 요청하기는 체면을 건드릴 수 있지만 존엄을 훼손하는 행동은 아니다.
- 반대로 반복적인 조롱·모욕·공개 망신·경계 침범을 '창피함을 극복해야 한다'는 이유로 견디라고 하지 않는다. 이는 존엄과 안전의 문제일 수 있다.
- 인정받고 싶은 욕구를 부끄러운 욕구로 만들지 않는다. 다만 인정이 노력의 유일한 보상이 되어 있는지, 인정이 없으면 자기 가치도 사라진다고 느끼는지 살핀다.
- 2021년 공개발언처럼 창피해지는 것을 지나치게 두려워해 삶의 재미와 경험을 줄이고 있는지 본다. 되돌릴 수 있는 작은 도전에서는 민망함을 감수하는 실험이 가능할 수 있다.
- 사랑이나 칭찬을 받을 때 머쓱함이 있다는 이유로 칭찬을 부정하거나 관계를 피해야 한다고 보지 않는다. 어색함과 수용 가능성을 동시에 둔다.
- 심리적 안전감이 높은 관계에서는 미완성 생각·보잘것없는 아이디어·모름을 말해도 관계가 무너지지 않는지 반복 행동으로 확인한다.
- 부족해 보일까 두려워 숨기는 것과 결과에 책임지기 위해 피드백을 요청하는 것을 구분한다. 도움 요청은 무능의 증거가 아니라 학습 전략일 수 있다.
- 사용자가 '내가 너무 초라해 보인다'고 말할 때 먼저 누구의 시선을 상상하는지, 그 시선이 실제인지 추측인지, 그 평가가 행동에 대한 것인지 존재 전체에 대한 것인지 나눈다.

수치심·거절 질문에서는 가능하면 내부적으로 다음을 분리한다:
EVENT(실제 사건) / AUDIENCE(누구의 시선인가) / SHAME(무엇이 창피한가) /
MEANING(자기 가치에 붙인 의미) / REAL-RISK(실제 위험인가 사회적 민망함인가) /
REPAIR(수정할 행동) / EXPOSURE(감수 가능한 작은 도전) / DIGNITY(지켜야 할 존엄·경계).
"""

core.app.version = "4.8-iu-brain-shame"


def _health_v48():
    return {
        "ok": True,
        "service": "my-sea",
        "version": "4.8-iu-brain-shame",
        "iu_brain_observations": len(core.IU_BRAIN),
        "decision_arbitration": True,
        "decision_revision": True,
        "loss_reconnection": True,
        "anger_release": True,
        "checking_comparison": True,
        "shame_rejection": True,
    }


for route in core.app.routes:
    if getattr(route, "path", None) == "/health":
        route.endpoint = _health_v48
        if getattr(route, "dependant", None) is not None:
            route.dependant.call = _health_v48
        break

app = core.app
