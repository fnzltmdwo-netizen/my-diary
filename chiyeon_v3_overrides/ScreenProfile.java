package com.chiyeon.overlay;

import java.util.Locale;

enum ScreenProfile {
    HOME(
        "일일", 0xF9FFF4F8, 0xFFD95B8A, 0xFF4D2938, false, false,
        "오늘 쓴 거 또 숨길 생각은 아니지? 👀",
        "작은 지출이라고 봐주는 거 없어. 다 쌓여 😏",
        "오늘 장부부터 보자. 돈은 기억보다 기록이 정확해.",
        "얼마 안 썼다고 생각할 때가 제일 위험해."
    ),
    CALENDAR(
        "달력", 0xF9F7F3FF, 0xFF8C70CB, 0xFF44345B, true, false,
        "달력으로 보면 소비 습관이 딱 들켜 😌",
        "며칠 몰아서 쓰는지 여기선 다 보여.",
        "빈 날이 많으면 잘한 거고, 빽빽하면 나랑 얘기 좀 하자.",
        "날짜로 보면 충동인지 습관인지 금방 보여 👀"
    ),
    MONTHLY(
        "월별", 0xF9F1F8FF, 0xFF5799CB, 0xFF274A63, false, false,
        "한 달치 모아놓으면 핑계가 안 통하지 👀",
        "이번 달 돈 어디로 갔는지 같이 까보자.",
        "월별로 보면 새는 구멍이 생각보다 선명해.",
        "잘 쓴 돈이랑 그냥 샌 돈, 이제 구분해보자."
    ),
    SETTLEMENT(
        "결산", 0xF9FFF8EE, 0xFFD89748, 0xFF65431F, true, false,
        "결산 시간. 잘 쓴 돈이랑 새버린 돈 갈라보자 😎",
        "이번 달은 변명 말고 결과표 보는 날이야.",
        "끝난 달은 혼내는 게 아니라 다음 달에 덜 새게 보는 거야.",
        "잘한 건 인정하고, 새버린 건 다음 달에 막자."
    ),
    MEMO(
        "치연 메모", 0xF9FFF5F8, 0xFFD36D96, 0xFF5B3042, false, false,
        "왜 썼는지 적어두면 다음엔 덜 흔들려.",
        "돈도 감정 따라 움직여. 메모가 힌트야.",
        "나중에 ‘이거 왜 샀지?’ 하지 말고 지금 한 줄만 🙄",
        "소비 이유까지 적으면 네 패턴이 진짜 보여."
    ),
    STATS(
        "돈성적표", 0xF9EFF8FF, 0xFF4A94C8, 0xFF244A64, false, false,
        "그래프는 안 거짓말해. 이번 달 성적표 까보자 👀",
        "숫자 앞에서는 ‘얼마 안 썼는데’가 안 통하네? 😏",
        "어디에 돈이 몰렸는지 여기 보면 바로 보여.",
        "성적표는 혼내려고 보는 게 아니라 다음 달 덜 새게 보는 거야."
    ),
    ACCOUNTS(
        "내 돈", 0xF9F0FBF6, 0xFF54A77D, 0xFF28513B, true, false,
        "잔액만 보고 부자 된 줄 알지 마. 카드값도 네 돈이야 💸",
        "통장 숫자보다 빠져나갈 돈까지 같이 봐야 진짜 잔액이야.",
        "내 돈 화면에서는 희망회로 금지. 현실 숫자만 보자.",
        "있는 돈, 나갈 돈, 빚까지 같이 봐야 마음이 편해져."
    ),
    TRANSACTION(
        "거래 입력", 0xFAFFF8EB, 0xFFD88E3C, 0xFF64421F, false, true,
        "이거 진짜 필요한 지출 맞아? 😑",
        "저장 누르기 전에 양심 검사 한 번만.",
        "결제는 쉬워도 수습은 내가 해야 돼.",
        "얼마 썼어? 숨기지 말고 적어. 혼내는 건 그다음이야."
    ),
    MORE(
        "더보기", 0xF9F7F7F8, 0xFF888991, 0xFF3F4044, true, false,
        "여기서 또 뭐 건드리려고? 😌",
        "숨겨진 기능 찾는 건 좋은데 과소비 기능은 없어.",
        "설정 구경은 됐고, 장부도 한 번 보고 가.",
        "필요한 것만 만지고 너무 깊게 들어가진 마 ㅋㅋ"
    ),
    SETTINGS(
        "설정", 0xF9F7F7F8, 0xFF888991, 0xFF3F4044, true, true,
        "한 번 제대로 맞춰두면 나중에 덜 귀찮아.",
        "설정은 지금 귀찮고 나중엔 고마운 거야.",
        "백업 같은 건 미루지 말고 여기서 바로 해두자.",
        "숫자 기준 바꿨으면 나도 그 기준으로 볼게."
    ),
    SEARCH(
        "검색", 0xF9F1F6FF, 0xFF6B8BC3, 0xFF304567, false, true,
        "어디다 썼는지 기억 안 나지? 같이 찾아보자 🔎",
        "기억은 흐려져도 기록은 남아 있어.",
        "그 돈 어디 갔나 싶을 땐 검색이 제일 빨라.",
        "찾아보면 ‘아 맞다…’ 하는 지출 꼭 하나 나온다 ㅋㅋ"
    ),
    UNKNOWN(
        "치연", 0xF9FFF7FA, 0xFFD85A86, 0xFF552A3C, false, false,
        "치연 출근 완료. 네 돈 옆에 붙어 있을게 😎",
        "장부 열었네? 그럼 나도 같이 본다.",
        "오늘도 네 돈 지키러 왔어.",
        "숫자 숨겨도 소용없어. 나 다 볼 거야 👀"
    );

    final String label;
    final int background;
    final int accent;
    final int textColor;
    final boolean imageFirst;
    final boolean compactTop;
    final String[] lines;

    ScreenProfile(
        String label,
        int background,
        int accent,
        int textColor,
        boolean imageFirst,
        boolean compactTop,
        String... lines
    ) {
        this.label = label;
        this.background = background;
        this.accent = accent;
        this.textColor = textColor;
        this.imageFirst = imageFirst;
        this.compactTop = compactTop;
        this.lines = lines;
    }

    String pickLine(long salt) {
        if (lines == null || lines.length == 0) return "";
        long mixed = salt + (ordinal() * 37L);
        int idx = (int)Math.floorMod(mixed, lines.length);
        return lines[idx];
    }

    static ScreenProfile classify(String className, String visibleText) {
        String cls = safe(className);
        String text = safe(visibleText);

        // 거래 입력은 키보드/입력 이벤트가 많으므로 가장 먼저 잡는다.
        if ((text.contains("얼마 썼어") && text.contains("뭐 샀어")) ||
            (text.contains("언제") && text.contains("저장해") && text.contains("이체")) ||
            (text.contains("수입") && text.contains("지출") && text.contains("이체") && text.contains("반복/할부")) ||
            cls.contains("transaction") || cls.contains("write") || cls.contains("edit")) {
            return TRANSACTION;
        }

        // 접근성 노드가 선택 상태를 제공하면 이것을 최우선으로 사용한다.
        if (selected(text, "돈성적표")) return STATS;
        if (selected(text, "내 돈")) return ACCOUNTS;
        if (selected(text, "더보기")) return MORE;
        if (selected(text, "치연장부")) return HOME;
        if (selected(text, "치연 메모")) return MEMO;
        if (selected(text, "결산")) return SETTLEMENT;
        if (selected(text, "월별")) return MONTHLY;
        if (selected(text, "달력")) return CALENDAR;
        if (selected(text, "일일")) return HOME;

        // 현재 치연 돈관리 실제 UI의 고유 조합을 일반 키워드 점수보다 먼저 판정한다.
        if (text.contains("돈성적표") && text.contains("월간") &&
            (text.contains("100.0") || text.contains("%") || text.contains("그래프") || text.contains("식비"))) {
            return STATS;
        }

        if (text.contains("내 돈") &&
            (text.contains("잔액") || text.contains("자산") || text.contains("통장") ||
             text.contains("카드값") || text.contains("계좌"))) {
            return ACCOUNTS;
        }

        if (text.contains("치연 메모") &&
            (text.contains("아무것도 없네") || text.contains("메모") || text.contains("노트"))) {
            return MEMO;
        }

        if (text.contains("치연장부") && text.contains("돈성적표") &&
            text.contains("내 돈") && text.contains("더보기") &&
            text.contains("일일") && text.contains("달력") && text.contains("월별") &&
            text.contains("수입") && text.contains("지출") && text.contains("합계")) {
            return HOME;
        }

        if (text.contains("결산") && (text.contains("이번 달") || text.contains("정산"))) return SETTLEMENT;
        if (text.contains("달력") && (text.contains("일 월 화 수 목 금 토") || text.contains("캘린더"))) return CALENDAR;
        if (text.contains("월별") && (text.contains("월간") || text.contains("카테고리"))) return MONTHLY;

        int settings = score(cls, text,
            new String[]{"setting", "preference", "config"},
            new String[]{"환경설정", "백업", "복원", "통화", "알림", "잠금", "setting", "backup"});
        int search = score(cls, text,
            new String[]{"search"},
            new String[]{"검색", "찾기", "search"});
        int memo = score(cls, text,
            new String[]{"memo", "note"},
            new String[]{"치연 메모", "메모장", "노트"});
        int settlement = score(cls, text,
            new String[]{"settle", "summary"},
            new String[]{"결산", "정산"});
        int monthly = score(cls, text,
            new String[]{"month", "monthly"},
            new String[]{"월별", "월간"});
        int calendar = score(cls, text,
            new String[]{"calendar"},
            new String[]{"달력", "캘린더", "calendar"});
        int stats = score(cls, text,
            new String[]{"stat", "chart", "analysis"},
            new String[]{"돈성적표", "통계", "분석", "차트", "그래프", "statistics", "stats", "100.0", "%"});
        int accounts = score(cls, text,
            new String[]{"account", "asset", "card"},
            new String[]{"내 돈", "계정", "자산", "카드값", "현금", "은행", "잔액", "account", "asset"});
        int more = score(cls, text,
            new String[]{"more"},
            new String[]{"더보기"});
        int home = score(cls, text,
            new String[]{"main", "home", "daily"},
            new String[]{"일일", "오늘", "거래내역", "daily", "home"});

        int best = 0;
        ScreenProfile result = UNKNOWN;
        if (home > best) { best = home; result = HOME; }
        if (accounts > best) { best = accounts; result = ACCOUNTS; }
        if (stats > best) { best = stats; result = STATS; }
        if (calendar > best) { best = calendar; result = CALENDAR; }
        if (monthly > best) { best = monthly; result = MONTHLY; }
        if (settlement > best) { best = settlement; result = SETTLEMENT; }
        if (memo > best) { best = memo; result = MEMO; }
        if (more > best) { best = more; result = MORE; }
        if (search > best) { best = search; result = SEARCH; }
        if (settings > best) { best = settings; result = SETTINGS; }
        return result;
    }

    private static boolean selected(String text, String word) {
        return text.contains("선택됨:" + word) || text.contains("selected:" + word);
    }

    private static int score(String cls, String text, String[] classWords, String[] textWords) {
        int score = 0;
        for (String w : classWords) if (cls.contains(w)) score += 4;
        for (String w : textWords) if (text.contains(w)) score += 1;
        return score;
    }

    private static String safe(String value) {
        return value == null ? "" : value.toLowerCase(Locale.ROOT);
    }
}
