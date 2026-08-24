package com.chiyeon.overlay;

import android.accessibilityservice.AccessibilityService;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.graphics.PixelFormat;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Handler;
import android.os.Looper;
import android.view.Gravity;
import android.view.View;
import android.view.WindowManager;
import android.view.accessibility.AccessibilityEvent;
import android.view.accessibility.AccessibilityNodeInfo;
import android.view.accessibility.AccessibilityWindowInfo;
import android.view.animation.DecelerateInterpolator;
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;

import java.util.ArrayDeque;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

public class ChiyeonAccessibilityService extends AccessibilityService {
    static final String PREFS = "chiyeon_overlay_status";

    private static final long PROFILE_STABLE_MS = 650L;
    private static final long MIN_PROFILE_HOLD_MS = 2200L;
    private static final long LEAVE_GRACE_MS = 2400L;
    private static final long REFRESH_INTERVAL_MS = 320L;

    private WindowManager wm;
    private FrameLayout overlayRoot;
    private LinearLayout card;
    private LinearLayout contentRow;
    private LinearLayout textBox;
    private View accentBar;
    private TextView message;
    private TextView badge;
    private ImageView image;

    private boolean visible = false;
    private ScreenProfile currentProfile = ScreenProfile.UNKNOWN;
    private ScreenProfile displayedProfile = ScreenProfile.UNKNOWN;
    private ScreenProfile pendingProfile = null;
    private WindowManager.LayoutParams overlayParams;

    private long lastRefresh = 0L;
    private long lastTargetSeenAt = 0L;
    private long lastProfileAppliedAt = 0L;

    private final Handler handler = new Handler(Looper.getMainLooper());
    private Runnable pendingApply;
    private String pendingPkg = "";
    private String pendingCls = "";
    private String pendingText = "";

    private final Set<String> targets = new HashSet<>(Arrays.asList(
        "com.realbyteapps.moneymanager",
        "com.realbyteapps.moneymanagerfree",
        "com.realbyteapps.moneya",
        "com.realbyte.money",
        "com.chiyeon.moneybook",
        "com.chiyeon.money"
    ));

    private final Set<String> transientPackages = new HashSet<>(Arrays.asList(
        "android",
        "com.android.systemui",
        "com.samsung.android.honeyboard",
        "com.google.android.inputmethod.latin",
        "com.sec.android.inputmethod",
        "com.samsung.android.sidegesturerender",
        "com.samsung.android.app.smartcapture",
        "com.samsung.android.app.cocktailbarservice"
    ));

    private int dp(float v) {
        return (int)(v * getResources().getDisplayMetrics().density + 0.5f);
    }

    @Override
    public void onServiceConnected() {
        super.onServiceConnected();
        wm = (WindowManager)getSystemService(WINDOW_SERVICE);
        buildOverlay();
        saveState("서비스 연결됨 · V6 POLISHED", "", "", ScreenProfile.UNKNOWN, "");
    }

    private void buildOverlay() {
        overlayRoot = new FrameLayout(this);
        overlayRoot.setPadding(dp(16), dp(7), dp(16), dp(7));
        overlayRoot.setClipChildren(false);
        overlayRoot.setClipToPadding(false);

        card = new LinearLayout(this);
        card.setOrientation(LinearLayout.HORIZONTAL);
        card.setGravity(Gravity.CENTER_VERTICAL);
        card.setPadding(dp(12), dp(10), dp(12), dp(10));
        card.setClipChildren(false);
        card.setClipToPadding(false);
        card.setElevation(dp(9));

        accentBar = new View(this);

        contentRow = new LinearLayout(this);
        contentRow.setOrientation(LinearLayout.HORIZONTAL);
        contentRow.setGravity(Gravity.CENTER_VERTICAL);

        image = new ImageView(this);
        image.setImageResource(R.drawable.chiyeon);
        image.setScaleType(ImageView.ScaleType.CENTER_INSIDE);
        image.setAlpha(0.98f);

        textBox = new LinearLayout(this);
        textBox.setOrientation(LinearLayout.VERTICAL);
        textBox.setGravity(Gravity.CENTER_VERTICAL);

        badge = new TextView(this);
        badge.setTextSize(10.0f);
        badge.setGravity(Gravity.CENTER);
        badge.setIncludeFontPadding(false);
        badge.setTypeface(Typeface.create("sans-serif-medium", Typeface.NORMAL));
        badge.setPadding(dp(8), dp(3), dp(8), dp(3));

        message = new TextView(this);
        message.setTextSize(14.0f);
        message.setGravity(Gravity.CENTER_VERTICAL);
        message.setMaxLines(2);
        message.setIncludeFontPadding(false);
        message.setLineSpacing(dp(1), 1.04f);
        message.setTypeface(Typeface.create("sans-serif", Typeface.NORMAL));
        message.setPadding(0, dp(5), 0, 0);

        textBox.addView(badge, new LinearLayout.LayoutParams(-2, -2));
        textBox.addView(message, new LinearLayout.LayoutParams(-1, -2));

        LinearLayout.LayoutParams barParams = new LinearLayout.LayoutParams(dp(4), dp(46));
        barParams.setMarginEnd(dp(10));
        card.addView(accentBar, barParams);
        card.addView(contentRow, new LinearLayout.LayoutParams(0, -2, 1f));

        FrameLayout.LayoutParams cp = new FrameLayout.LayoutParams(-1, -2);
        cp.gravity = Gravity.CENTER;
        overlayRoot.addView(card, cp);

        renderProfile(ScreenProfile.UNKNOWN, true);
    }

    private WindowManager.LayoutParams makeParams(ScreenProfile profile) {
        boolean top = profile != null && profile.compactTop;
        WindowManager.LayoutParams p = new WindowManager.LayoutParams(
            WindowManager.LayoutParams.MATCH_PARENT,
            dp(top ? 78 : 104),
            WindowManager.LayoutParams.TYPE_ACCESSIBILITY_OVERLAY,
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE |
                WindowManager.LayoutParams.FLAG_NOT_TOUCHABLE |
                WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS |
                WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN,
            PixelFormat.TRANSLUCENT
        );
        p.gravity = (top ? Gravity.TOP : Gravity.BOTTOM) | Gravity.CENTER_HORIZONTAL;
        p.x = 0;
        p.y = dp(top ? 68 : 86);
        return p;
    }

    private void renderProfile(ScreenProfile profile, boolean chooseNewLine) {
        if (profile == null) profile = ScreenProfile.UNKNOWN;

        boolean top = profile.compactTop;
        card.setPadding(dp(top ? 10 : 12), dp(top ? 7 : 10), dp(top ? 10 : 12), dp(top ? 7 : 10));
        card.setElevation(dp(top ? 6 : 9));

        GradientDrawable bg = new GradientDrawable();
        bg.setColor(profile.background);
        bg.setCornerRadius(dp(top ? 18 : 24));
        bg.setStroke(dp(1.15f), withAlpha(profile.accent, 220));
        card.setBackground(bg);

        GradientDrawable bar = new GradientDrawable();
        bar.setColor(withAlpha(profile.accent, 225));
        bar.setCornerRadius(dp(20));
        accentBar.setBackground(bar);
        LinearLayout.LayoutParams barLp = (LinearLayout.LayoutParams)accentBar.getLayoutParams();
        if (barLp != null) {
            barLp.width = dp(top ? 3 : 4);
            barLp.height = dp(top ? 34 : 46);
            barLp.setMarginEnd(dp(top ? 8 : 10));
            accentBar.setLayoutParams(barLp);
        }

        GradientDrawable chip = new GradientDrawable();
        chip.setColor(withAlpha(profile.accent, 30));
        chip.setCornerRadius(dp(20));
        badge.setBackground(chip);
        badge.setTextColor(profile.accent);
        badge.setText("치연  ·  " + profile.label);
        badge.setTextSize(top ? 9.4f : 10.0f);

        message.setTextColor(profile.textColor);
        message.setTextSize(top ? 12.7f : 14.0f);
        if (chooseNewLine || message.getText() == null || message.getText().length() == 0) {
            long salt = System.currentTimeMillis() / 1000L;
            message.setText(profile.pickLine(salt));
        }

        contentRow.removeAllViews();
        int iw = top ? 48 : 68;
        int ih = top ? 56 : 82;

        LinearLayout.LayoutParams imageLp = new LinearLayout.LayoutParams(dp(iw), dp(ih));
        LinearLayout.LayoutParams textLp = new LinearLayout.LayoutParams(0, -2, 1f);

        if (profile.imageFirst) {
            imageLp.setMarginEnd(dp(top ? 7 : 9));
            contentRow.addView(image, imageLp);
            contentRow.addView(textBox, textLp);
        } else {
            imageLp.setMarginStart(dp(top ? 7 : 9));
            contentRow.addView(textBox, textLp);
            contentRow.addView(image, imageLp);
        }
    }

    private void applyProfile(final ScreenProfile profile, boolean force, boolean animate) {
        final ScreenProfile next = profile == null ? ScreenProfile.UNKNOWN : profile;
        if (!force && next == currentProfile) return;

        if (animate && visible) {
            card.animate().cancel();
            final float outY = next.compactTop ? -dp(5) : dp(5);
            card.animate()
                .alpha(0.12f)
                .translationY(outY)
                .setDuration(90L)
                .withEndAction(new Runnable() {
                    @Override public void run() {
                        currentProfile = next;
                        renderProfile(next, true);
                        updateOverlayLayout(next);
                        card.setAlpha(0.12f);
                        card.setTranslationY(next.compactTop ? -dp(5) : dp(5));
                        card.animate()
                            .alpha(1f)
                            .translationY(0f)
                            .setDuration(180L)
                            .setInterpolator(new DecelerateInterpolator())
                            .start();
                    }
                })
                .start();
        } else {
            currentProfile = next;
            renderProfile(next, true);
            if (visible) updateOverlayLayout(next);
        }
    }

    private void updateOverlayLayout(ScreenProfile profile) {
        if (!visible || wm == null || overlayRoot == null) return;
        try {
            overlayParams = makeParams(profile);
            wm.updateViewLayout(overlayRoot, overlayParams);
        } catch (Exception ignored) {}
    }

    private static int withAlpha(int color, int alpha) {
        return Color.argb(alpha, Color.red(color), Color.green(color), Color.blue(color));
    }

    private void show() {
        if (visible || overlayRoot == null || wm == null) return;
        try {
            currentProfile = displayedProfile == null ? ScreenProfile.UNKNOWN : displayedProfile;
            renderProfile(currentProfile, false);
            overlayParams = makeParams(currentProfile);

            overlayRoot.setAlpha(0f);
            overlayRoot.setTranslationY(currentProfile.compactTop ? -dp(12) : dp(14));
            wm.addView(overlayRoot, overlayParams);
            visible = true;

            overlayRoot.animate()
                .alpha(1f)
                .translationY(0f)
                .setDuration(220L)
                .setInterpolator(new DecelerateInterpolator())
                .start();
        } catch (Exception e) {
            saveState("오버레이 표시 실패 · V6", "", e.getClass().getSimpleName(), ScreenProfile.UNKNOWN, "");
        }
    }

    private void cancelPendingProfile() {
        if (pendingApply != null) handler.removeCallbacks(pendingApply);
        pendingApply = null;
        pendingProfile = null;
        pendingPkg = "";
        pendingCls = "";
        pendingText = "";
    }

    private void queueProfile(ScreenProfile next, String pkg, String cls, String visibleText) {
        if (next == null) next = ScreenProfile.UNKNOWN;

        // 이미 안정적으로 표시 중인 프로필로 되돌아온 이벤트면 후보 전환을 취소한다.
        if (next == displayedProfile) {
            cancelPendingProfile();
            return;
        }

        // 알려진 화면을 표시 중일 때 UNKNOWN 한두 번 들어오는 것은 무시한다.
        if (next == ScreenProfile.UNKNOWN && displayedProfile != ScreenProfile.UNKNOWN) return;

        pendingPkg = pkg == null ? "" : pkg;
        pendingCls = cls == null ? "" : cls;
        pendingText = visibleText == null ? "" : visibleText;

        if (pendingProfile != next) {
            pendingProfile = next;
            schedulePendingApply(PROFILE_STABLE_MS);
        }
    }

    private void schedulePendingApply(long delayMs) {
        if (pendingApply != null) handler.removeCallbacks(pendingApply);

        pendingApply = new Runnable() {
            @Override public void run() {
                if (pendingProfile == null) return;

                long now = System.currentTimeMillis();
                if (now - lastTargetSeenAt > LEAVE_GRACE_MS) {
                    cancelPendingProfile();
                    return;
                }

                long heldFor = now - lastProfileAppliedAt;
                if (lastProfileAppliedAt > 0L && heldFor < MIN_PROFILE_HOLD_MS) {
                    schedulePendingApply(MIN_PROFILE_HOLD_MS - heldFor);
                    return;
                }

                ScreenProfile next = pendingProfile;
                String pkg = pendingPkg;
                String cls = pendingCls;
                String text = pendingText;

                pendingProfile = null;
                pendingApply = null;
                pendingPkg = "";
                pendingCls = "";
                pendingText = "";

                applyProfile(next, false, true);
                displayedProfile = next;
                lastProfileAppliedAt = System.currentTimeMillis();
                saveState("치연 돈관리 감지됨 · V6 안정 전환", pkg, cls, next, text);
            }
        };

        handler.postDelayed(pendingApply, Math.max(0L, delayMs));
    }

    private void hide() {
        cancelPendingProfile();
        if (visible && overlayRoot != null && wm != null) {
            try { wm.removeView(overlayRoot); } catch (Exception ignored) {}
        }
        visible = false;
        currentProfile = ScreenProfile.UNKNOWN;
        displayedProfile = ScreenProfile.UNKNOWN;
        lastProfileAppliedAt = 0L;
        overlayParams = null;
    }

    @Override
    public void onAccessibilityEvent(AccessibilityEvent event) {
        if (event == null) return;

        CharSequence pkgCs = event.getPackageName();
        String pkg = pkgCs == null ? "" : pkgCs.toString();
        String cls = event.getClassName() == null ? "" : event.getClassName().toString();
        long now = System.currentTimeMillis();

        AccessibilityNodeInfo moneyRoot = findMoneyManagerRoot();
        boolean eventIsTarget = isTargetPackage(pkg);

        if (eventIsTarget || moneyRoot != null) {
            lastTargetSeenAt = now;
            show();

            int type = event.getEventType();
            boolean importantEvent =
                type == AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED ||
                type == AccessibilityEvent.TYPE_VIEW_CLICKED ||
                type == AccessibilityEvent.TYPE_VIEW_SELECTED;

            if (importantEvent || now - lastRefresh >= REFRESH_INTERVAL_MS) {
                lastRefresh = now;

                AccessibilityNodeInfo root = moneyRoot != null ? moneyRoot : getRootInActiveWindow();
                String visibleText = collectVisibleText(root);
                String targetPkg = packageOf(root);
                if (targetPkg.isEmpty() && eventIsTarget) targetPkg = pkg;

                ScreenProfile profile = ScreenProfile.classify(cls, visibleText);
                queueProfile(profile, targetPkg, cls, visibleText);
            }
            return;
        }

        if (isTransientPackage(pkg) || pkg.equals(getPackageName())) return;
        if (now - lastTargetSeenAt < LEAVE_GRACE_MS) return;

        if (event.getEventType() == AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED) {
            hide();
            saveState("치연 돈관리 밖으로 이동 · V6", pkg, cls, ScreenProfile.UNKNOWN, "");
        }
    }

    private boolean isTargetPackage(String pkg) {
        if (pkg == null || pkg.isEmpty()) return false;
        if (targets.contains(pkg)) return true;
        String p = pkg.toLowerCase();
        return p.startsWith("com.realbyteapps.money") ||
               p.startsWith("com.chiyeon.money");
    }

    private boolean isTransientPackage(String pkg) {
        if (pkg == null || pkg.isEmpty()) return true;
        if (transientPackages.contains(pkg)) return true;
        String p = pkg.toLowerCase();
        return p.contains("sidegesture") ||
               p.contains("inputmethod") ||
               p.contains("keyboard") ||
               p.contains("smartcapture") ||
               p.contains("systemui");
    }

    private AccessibilityNodeInfo findMoneyManagerRoot() {
        AccessibilityNodeInfo active = getRootInActiveWindow();
        if (isTargetRoot(active)) return active;

        try {
            List<AccessibilityWindowInfo> windows = getWindows();
            if (windows != null) {
                for (AccessibilityWindowInfo window : windows) {
                    if (window == null) continue;
                    AccessibilityNodeInfo root = window.getRoot();
                    if (isTargetRoot(root)) return root;
                }
            }
        } catch (Exception ignored) {}
        return null;
    }

    private boolean isTargetRoot(AccessibilityNodeInfo root) {
        return root != null && isTargetPackage(packageOf(root));
    }

    private String packageOf(AccessibilityNodeInfo root) {
        if (root == null || root.getPackageName() == null) return "";
        return root.getPackageName().toString();
    }

    private String collectVisibleText(AccessibilityNodeInfo root) {
        if (root == null) return "";

        StringBuilder out = new StringBuilder();
        ArrayDeque<AccessibilityNodeInfo> q = new ArrayDeque<>();
        q.add(root);
        int visited = 0;

        while (!q.isEmpty() && visited < 220 && out.length() < 5200) {
            AccessibilityNodeInfo node = q.removeFirst();
            visited++;

            CharSequence nodeText = node.getText();
            CharSequence nodeDesc = node.getContentDescription();
            append(out, nodeText);
            append(out, nodeDesc);

            CharSequence selectedLabel = nodeText != null ? nodeText : nodeDesc;
            if ((node.isSelected() || node.isChecked()) && selectedLabel != null) {
                append(out, "선택됨:" + selectedLabel.toString());
            }

            String viewId = node.getViewIdResourceName();
            if (viewId != null && (node.isSelected() || node.isChecked())) {
                append(out, "id:" + viewId);
            }

            int count = node.getChildCount();
            for (int i = 0; i < count; i++) {
                AccessibilityNodeInfo child = node.getChild(i);
                if (child != null) q.addLast(child);
            }
        }
        return out.toString();
    }

    private void append(StringBuilder out, CharSequence value) {
        if (value == null) return;
        String s = value.toString().trim();
        if (s.isEmpty()) return;
        if (out.length() > 0) out.append(" | ");
        out.append(s);
    }

    private void saveState(String state, String pkg, String cls, ScreenProfile profile, String visibleText) {
        SharedPreferences sp = getSharedPreferences(PREFS, MODE_PRIVATE);
        String sample = visibleText == null ? "" : visibleText;
        if (sample.length() > 700) sample = sample.substring(0, 700);

        sp.edit()
            .putString("state", state)
            .putString("package", pkg)
            .putString("class", cls)
            .putString("profile", profile == null ? "" : profile.label)
            .putString("sample", sample)
            .putLong("time", System.currentTimeMillis())
            .apply();
    }

    @Override public void onInterrupt() { hide(); }

    @Override
    public void onDestroy() {
        cancelPendingProfile();
        hide();
        super.onDestroy();
    }
}
