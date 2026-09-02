"""IU Brain v4.9 — uncertainty / waiting / control / flexibility layer.

Builds on v4.8 shame-rejection. This layer improves retrieval and prompting for
uncertainty, ambiguous situations, future worry, waiting, planning, control,
and adaptive flexibility.

Public IU evidence is strongest for preparation, prediction error, controllable
effort, rules, and flexibility. Time-boxed waiting/review-point guidance is a
research decision framework, not a direct IU doctrine.
"""

from backend import main_v48 as v48

core = v48.core

UNCERTAINTY_ALIASES = {
    "불확실": ["uncertainty", "ambiguity", "control", "flexibility", "preparation"],
    "모르겠": ["uncertainty", "ambiguity", "unknown", "decision", "acceptance"],
    "모르겠어": ["uncertainty", "ambiguity", "unknown", "decision", "acceptance"],
    "답이 없": ["uncertainty", "waiting", "ambiguity", "acceptance", "time"],
    "답을 모르": ["uncertainty", "unknown", "decision", "acceptance"],
    "확답": ["certainty-seeking", "uncertainty", "waiting", "relationships"],
    "확실하지": ["uncertainty", "certainty-seeking", "ambiguity", "decision"],
    "확실해져야": ["certainty-seeking", "action", "experimentation", "uncertainty"],
    "기다려": ["waiting", "patience", "uncertainty", "time", "new-data"],
    "기다리": ["waiting", "patience", "uncertainty", "time", "new-data"],
    "기다릴까": ["waiting", "decision", "timebox", "new-data", "limits"],
    "언제까지": ["waiting", "timebox", "uncertainty", "limits", "decision"],
    "조급": ["impatience", "waiting", "uncertainty", "attention"],
    "조바심": ["impatience", "waiting", "uncertainty", "attention"],
    "답답": ["uncertainty", "waiting", "emotion", "control"],
    "미래 걱정": ["future", "uncertainty", "worry", "control", "forecast"],
    "미래가": ["future", "uncertainty", "worry", "forecast"],
    "앞으로 어떻게": ["future", "uncertainty", "forecast", "decision"],
    "어떻게 될": ["future", "uncertainty", "prediction", "openness"],
    "결과를 모르": ["uncertainty", "outcome", "control", "effort"],
    "결과가 어떻게": ["uncertainty", "outcome", "forecast", "control"],
    "계획대로": ["planning", "flexibility", "revision", "adaptation"],
    "계획이 틀": ["planning", "flexibility", "revision", "adaptation"],
    "계획 어긋": ["planning", "flexibility", "revision", "adaptation"],
    "계획이 바뀌": ["planning", "revision", "flexibility", "new-evidence"],
    "통제": ["control", "limits", "uncertainty", "letting-go"],
    "컨트롤": ["control", "limits", "uncertainty", "letting-go"],
    "예상": ["forecast", "prediction-error", "uncertainty", "updating"],
    "예측": ["forecast", "prediction-error", "uncertainty", "updating"],
    "변수": ["uncertainty", "control", "adaptation", "new-data"],
    "애매": ["ambiguity", "uncertainty", "decision", "acceptance"],
    "보장": ["certainty-seeking", "uncertainty", "risk", "outcome"],
    "장담": ["certainty-seeking", "uncertainty", "forecast", "risk"],
    "안심이 안": ["uncertainty", "certainty-seeking", "worry", "control"],
}

core.TOPIC_ALIASES.update(UNCERTAINTY_ALIASES)

UNCERTAINTY_QUERY_TRIGGERS = tuple(UNCERTAINTY_ALIASES.keys()) + (
    "알 수 없", "뭘 해야 할지", "결정을 못", "확신이 없", "확신이 안",
    "답을 기다", "연락 기다", "언젠가", "혹시나", "만약에", "될까 봐",
)

UNCERTAINTY_ENRICHMENT = (
    " uncertainty ambiguity unknown planning preparation flexibility control waiting patience"
    " future forecast prediction-error new-data revision adaptation values methods timebox"
    " experiment action acceptance letting-go certainty-seeking outcome effort limits openness"
)

_original_retrieve = core.retrieve_iu_evidence


def retrieve_iu_evidence_v49(message: str, context: dict | None, limit: int = 14):
    text = (message or "").lower()
    if any(trigger in text for trigger in UNCERTAINTY_QUERY_TRIGGERS):
        enriched = f"{message}\n[uncertainty/control retrieval hints:{UNCERTAINTY_ENRICHMENT}]"
        return _original_retrieve(enriched, context, limit)
    return _original_retrieve(message, context, limit)


core.retrieve_iu_evidence = retrieve_iu_evidence_v49

core.IU_SYSTEM += """

불확실성·기다림·미래걱정·통제 관련 추가 원칙:
- 사용자를 안심시키기 위해 근거 없는 확신을 만들어내지 않는다. 현재 모르는 것은 모른다고 말하고, 확인된 사실과 예측을 분리한다.
- UNKNOWN(모름)을 DANGER(위험), REJECTION(거절), FAILURE(실패)와 자동 등식으로 두지 않는다.
- 현재 정보가 아직 없는 것과 원리적으로 알 수 없는 것을 구분한다. 전자는 새 정보가 생길 조건을 찾고, 후자는 불확실성을 완전히 제거하려는 시도를 줄일 수 있다.
- 준비와 통제를 구분한다. 준비는 선택지를 늘리고 대응력을 높일 수 있지만 미래 결과를 보장하지 않는다.
- 사용자가 통제 가능한 행동·경계·준비·질문과 통제하기 어려운 타인의 반응·우연·결과를 나눠 본다.
- 중요한 가치와 구체적 방법을 분리한다. 가치가 유지되더라도 계획·방법·순서는 새 정보에 따라 수정할 수 있다.
- 계획이 바뀌었다는 이유만으로 실패나 변덕으로 해석하지 않는다. 반대로 새 정보 없이 불안만 커질 때마다 계획을 반복해서 갈아엎도록 권하지 않는다.
- 기다림 자체를 사랑·인내·성숙의 증거로 미화하지 않는다. 기다릴 이유, 새 정보가 올 조건, 기다림의 비용, 다시 검토할 시점을 확인한다.
- `언제까지 기다릴지` 같은 시간 제한 규칙은 아이유의 직접 공개발언이 아니라 연구용 의사결정 프레임임을 필요할 때 구분한다.
- 새 정보가 생길 가능성과 리뷰 시점이 있는 기다림(ACTIVE WAIT)과, 무엇이 달라질지 없이 확답만 기다리는 상태(INDEFINITE WAIT)를 구분한다.
- 더 많은 확인이 새 정보를 만들지 않는다면 v4.7의 확인욕구/주의력 회수 원칙을 함께 적용한다. 반복 확인을 정보 수집으로 자동 정당화하지 않는다.
- 되돌릴 수 있는 작은 행동으로 실제 정보를 얻을 수 있다면 완전한 확신을 기다리기보다 작은 실험을 고려할 수 있다.
- 관계의 침묵·무응답·거리감에서 상대의 숨은 생각을 사실처럼 채워 넣지 않는다. 현재 행동 데이터와 아직 모르는 부분을 분리한다.
- 현재 관계 상태나 현재 감정을 미래의 영구 상태로 예언하지 않는다. 동시에 근거 없는 낙관으로 현재의 반복 행동을 무시하지 않는다.
- 아이유 공개자료에서 강하게 확인되는 것은 준비·통제 가능한 노력·예측의 수정·유연함이다. 사용자의 의료·법률·재정 등 고위험 결정에서는 전문 정보와 현실 안전을 우선한다.

불확실성 질문에서는 가능하면 내부적으로 다음을 분리한다:
KNOWN(현재 아는 것) / UNKNOWN(아직 모르는 것) / FORECAST(내가 만든 미래예측) /
CONTROL(통제 가능한 것) / VALUE(지킬 기준) / WAIT-UNTIL(다시 볼 시점) /
NEXT-DATA(판단을 바꿀 새 정보) / ACTION(그 전까지 할 수 있는 행동).
"""

core.app.version = "4.9-iu-brain-uncertainty"


def _health_v49():
    return {
        "ok": True,
        "service": "my-sea",
        "version": "4.9-iu-brain-uncertainty",
        "iu_brain_observations": len(core.IU_BRAIN),
        "decision_arbitration": True,
        "decision_revision": True,
        "loss_reconnection": True,
        "anger_release": True,
        "checking_comparison": True,
        "shame_rejection": True,
        "uncertainty_control": True,
    }


for route in core.app.routes:
    if getattr(route, "path", None) == "/health":
        route.endpoint = _health_v49
        if getattr(route, "dependant", None) is not None:
            route.dependant.call = _health_v49
        break

app = core.app
