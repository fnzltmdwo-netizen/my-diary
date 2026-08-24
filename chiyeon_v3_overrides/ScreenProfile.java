package com.chiyeon.overlay;

import java.util.Locale;

enum ScreenProfile {
    HOME("일일", "오늘 기록부터 보자. 작은 지출도 쌓이면 티 난다 😏", 0xFFFFF1F6, 0xFFD85C8A, 0xFF5A273D, false, false),
    CALENDAR("달력", "달력으로 보면 소비 습관이 딱 들켜. 숨길 생각 마 😌", 0xFFF5F0FF, 0xFF8E6CCF, 0xFF44305E, true, false),
    MONTHLY("월별", "한 달치 모아놓으면 핑계가 안 통하지. 어디에 샜는지 보자 👀", 0xFFEFF8FF, 0xFF5596C8, 0xFF244A64, false, false),
    SETTLEMENT("결산", "결산 시간. 잘 쓴 돈이랑 새버린 돈, 내가 갈라줄게 😎", 0xFFFFF6EA, 0xFFD28B42, 0xFF65401F, true, false),
    MEMO("치연 메모", "메모까지 남겨. 나중에 '이거 왜 샀지?' 하지 말고 🙄", 0xFFFFF2F8, 0xFFD05D91, 0xFF5C2940, false, false),
    STATS("돈성적표", "그래프는 안 거짓말해. 이번 달 성적표 까보자 👀", 0xFFEFF8FF, 0xFF5596C8, 0xFF244A64, false, false),
    ACCOUNTS("내 돈", "잔액만 보고 부자 된 줄 알지 마. 카드값까지 봐야 진짜 내 돈이야 💸", 0xFFF0FBF6, 0xFF5EAC82, 0xFF28513B, true, false),
    TRANSACTION("거래 입력", "얼마 썼어? 숨기지 말고 적어. 내가 혼내는 건 그다음이야 😑", 0xFFFFF7E9, 0xFFD99443, 0xFF66451F, false, true),
    MORE("더보기", "설정 만지는 건 좋은데, 장부 기록부터 제대로 하고 와 😌", 0xFFF4F4F5, 0xFF8B8B91, 0xFF3E3E42, true, false),
    SETTINGS("설정", "한 번 제대로 맞춰두면 나중에 덜 귀찮아. 지금 해두자.", 0xFFF4F4F5, 0xFF8B8B91, 0xFF3E3E42, true, false),
    SEARCH("검색", "어디다 썼는지 기억 안 나지? 내가 같이 찾아줄게 🔎", 0xFFF0F6FF, 0xFF6E8FC8, 0xFF304567, false, false),
    UNKNOWN("머니매니저", "머니매니저 잡았다. 이번엔 안 놓친다 😎", 0xFFFFF8FB, 0xFFD95686, 0xFF552A3C, false, false);

    final String label;
    final String line;
    final int background;
    final int accent;
    final int textColor;
    final boolean imageFirst;
    final boolean compactTop;

    ScreenProfile(String label, String line, int background, int accent, int textColor,
                  boolean imageFirst, boolean compactTop) {
        this.label = label;
        this.line = line;
        this.background = background;
        this.accent = accent;
        this.textColor = textColor;
        this.imageFirst = imageFirst;
        this.compactTop = compactTop;
    }

    static ScreenProfile classify(String className, String visibleText) {
        String cls = safe(className);
        String text = safe(visibleText);

        if ((text.contains("얼마 썼어") && text.contains("뭐 샀어")) ||
            (text.contains("언제") && text.contains("저장해") && text.contains("이체")) ||
            cls.contains("transaction") || cls.contains("write") || cls.contains("edit")) {
            return TRANSACTION;
        }

        if (selected(text, "치연 메모")) return MEMO;
        if (selected(text, "결산")) return SETTLEMENT;
        if (selected(text, "월별")) return MONTHLY;
        if (selected(text, "달력")) return CALENDAR;
        if (selected(text, "일일")) return HOME;
        if (selected(text, "돈성적표")) return STATS;
        if (selected(text, "내 돈")) return ACCOUNTS;
        if (selected(text, "더보기")) return MORE;

        if (text.contains("치연장부") && text.contains("돈성적표") && text.contains("내 돈") && text.contains("더보기") &&
            text.contains("일일") && text.contains("수입") && text.contains("지출") && text.contains("합계")) {
            return HOME;
        }

        int settings = score(cls, text, new String[]{"setting", "preference", "config"}, new String[]{"환경설정", "백업", "복원", "통화", "알림", "잠금", "setting", "backup"});
        int search = score(cls, text, new String[]{"search"}, new String[]{"검색", "찾기", "search"});
        int memo = score(cls, text, new String[]{"memo", "note"}, new String[]{"치연 메모", "메모장", "노트"});
        int settlement = score(cls, text, new String[]{"settle", "summary"}, new String[]{"결산", "정산"});
        int monthly = score(cls, text, new String[]{"month", "monthly"}, new String[]{"월별", "월간"});
        int calendar = score(cls, text, new String[]{"calendar"}, new String[]{"달력", "캘린더", "calendar"});
        int stats = score(cls, text, new String[]{"stat", "chart", "analysis"}, new String[]{"돈성적표", "통계", "분석", "차트", "그래프", "statistics", "stats"});
        int accounts = score(cls, text, new String[]{"account", "asset", "card"}, new String[]{"내 돈", "계정", "자산", "카드", "현금", "은행", "잔액", "account", "asset"});
        int more = score(cls, text, new String[]{"more"}, new String[]{"더보기"});
        int home = score(cls, text, new String[]{"main", "home", "daily"}, new String[]{"일일", "오늘", "거래내역", "daily", "home"});

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
