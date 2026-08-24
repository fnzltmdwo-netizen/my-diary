package com.chiyeon.overlay;

import android.accessibilityservice.AccessibilityService;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.graphics.PixelFormat;
import android.graphics.drawable.GradientDrawable;
import android.provider.Settings;
import android.view.Gravity;
import android.view.WindowManager;
import android.view.accessibility.AccessibilityEvent;
import android.view.accessibility.AccessibilityNodeInfo;
import android.view.accessibility.AccessibilityWindowInfo;
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

    private WindowManager wm;
    private FrameLayout overlayRoot;
    private LinearLayout card;
    private TextView message;
    private TextView badge;
    private ImageView image;
    private boolean visible = false;
    private ScreenProfile currentProfile = null;
    private long lastRefresh = 0L;
    private long lastTargetSeenAt = 0L;
    private WindowManager.LayoutParams overlayParams;

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

    private int dp(float v){ return (int)(v * getResources().getDisplayMetrics().density + 0.5f); }

    @Override public void onServiceConnected() {
        super.onServiceConnected();
        wm = (WindowManager)getSystemService(WINDOW_SERVICE);
        buildOverlay();
        saveState("서비스 연결됨 · V5 PACKAGE MATCHER", "", "", ScreenProfile.UNKNOWN, "");
    }

    private void buildOverlay(){
        overlayRoot = new FrameLayout(this);
        overlayRoot.setPadding(dp(10), dp(4), dp(10), dp(4));

        card = new LinearLayout(this);
        card.setOrientation(LinearLayout.HORIZONTAL);
        card.setGravity(Gravity.CENTER_VERTICAL);
        card.setPadding(dp(12), dp(7), dp(11), dp(7));

        image = new ImageView(this);
        image.setImageResource(R.drawable.chiyeon);
        image.setScaleType(ImageView.ScaleType.CENTER_INSIDE);

        LinearLayout textBox = new LinearLayout(this);
        textBox.setOrientation(LinearLayout.VERTICAL);
        textBox.setGravity(Gravity.CENTER_VERTICAL);

        badge = new TextView(this);
        badge.setTextSize(9.5f);
        badge.setPadding(dp(7), dp(2), dp(7), dp(2));

        message = new TextView(this);
        message.setTextSize(13.2f);
        message.setGravity(Gravity.CENTER_VERTICAL);
        message.setMaxLines(2);
        message.setPadding(0, dp(3), 0, 0);

        textBox.addView(badge, new LinearLayout.LayoutParams(-2, -2));
        textBox.addView(message, new LinearLayout.LayoutParams(-1, -2));
        textBox.setTag("textBox");

        card.addView(textBox, new LinearLayout.LayoutParams(0, -2, 1f));
        card.addView(image, new LinearLayout.LayoutParams(dp(60), dp(70)));

        FrameLayout.LayoutParams cp = new FrameLayout.LayoutParams(-1, -2);
        cp.gravity = Gravity.CENTER;
        overlayRoot.addView(card, cp);
        applyProfile(ScreenProfile.UNKNOWN, true);
    }

    private WindowManager.LayoutParams makeParams(ScreenProfile profile){
        boolean top = profile != null && profile.compactTop;
        WindowManager.LayoutParams p = new WindowManager.LayoutParams(
            WindowManager.LayoutParams.MATCH_PARENT,
            dp(top ? 72 : 92),
            WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE |
                WindowManager.LayoutParams.FLAG_NOT_TOUCHABLE |
                WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
            PixelFormat.TRANSLUCENT
        );
        p.gravity = (top ? Gravity.TOP : Gravity.BOTTOM) | Gravity.CENTER_HORIZONTAL;
        p.x = 0;
        p.y = dp(top ? 52 : 92);
        return p;
    }

    private void applyProfile(ScreenProfile profile, boolean force){
        if (profile == null) profile = ScreenProfile.UNKNOWN;
        if (!force && profile == currentProfile) return;
        currentProfile = profile;

        GradientDrawable bg = new GradientDrawable();
        bg.setColor(profile.background);
        bg.setCornerRadius(dp(profile.compactTop ? 17 : 20));
        bg.setStroke(dp(1.2f), profile.accent);
        card.setBackground(bg);

        GradientDrawable chip = new GradientDrawable();
        chip.setColor(withAlpha(profile.accent, 32));
        chip.setCornerRadius(dp(20));
        badge.setBackground(chip);
        badge.setTextColor(profile.accent);
        badge.setText("치연 · " + profile.label);

        message.setTextColor(profile.textColor);
        message.setText(profile.line);
        message.setTextSize(profile.compactTop ? 12.5f : 13.2f);

        LinearLayout textBox = (LinearLayout) card.findViewWithTag("textBox");
        card.removeAllViews();
        int iw = profile.compactTop ? 48 : 60;
        int ih = profile.compactTop ? 56 : 70;
        LinearLayout.LayoutParams ip = new LinearLayout.LayoutParams(dp(iw), dp(ih));
        LinearLayout.LayoutParams tp = new LinearLayout.LayoutParams(0, -2, 1f);
        if (profile.imageFirst) {
            card.addView(image, ip);
            card.addView(textBox, tp);
        } else {
            card.addView(textBox, tp);
            card.addView(image, ip);
        }

        if (visible && wm != null) {
            try {
                overlayParams = makeParams(profile);
                wm.updateViewLayout(overlayRoot, overlayParams);
            } catch (Exception ignored) {}
        }
    }

    private static int withAlpha(int color, int alpha) {
        return Color.argb(alpha, Color.red(color), Color.green(color), Color.blue(color));
    }

    private void show(){
        if (visible || overlayRoot == null || !Settings.canDrawOverlays(this)) return;
        try {
            overlayParams = makeParams(currentProfile == null ? ScreenProfile.UNKNOWN : currentProfile);
            wm.addView(overlayRoot, overlayParams);
            visible = true;
        } catch (Exception e) {
            saveState("오버레이 표시 실패", "", e.getClass().getSimpleName(), ScreenProfile.UNKNOWN, "");
        }
    }

    private void hide(){
        if (!visible || overlayRoot == null) return;
        try { wm.removeView(overlayRoot); } catch (Exception ignored) {}
        visible = false;
        currentProfile = null;
        overlayParams = null;
    }

    @Override public void onAccessibilityEvent(AccessibilityEvent event) {
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

            if (event.getEventType() == AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED ||
                event.getEventType() == AccessibilityEvent.TYPE_VIEW_CLICKED ||
                now - lastRefresh >= 180L) {
                lastRefresh = now;
                AccessibilityNodeInfo root = moneyRoot != null ? moneyRoot : getRootInActiveWindow();
                String visibleText = collectVisibleText(root);
                String targetPkg = packageOf(root);
                if (targetPkg.isEmpty() && eventIsTarget) targetPkg = pkg;
                ScreenProfile profile = ScreenProfile.classify(cls, visibleText);
                applyProfile(profile, false);
                saveState("치연 돈관리 감지됨 · 오버레이 유지", targetPkg, cls, profile, visibleText);
            }
            return;
        }

        if (isTransientPackage(pkg) || pkg.equals(getPackageName())) return;
        if (now - lastTargetSeenAt < 2200L) return;

        if (event.getEventType() == AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED) {
            hide();
            saveState("치연 돈관리 밖으로 이동", pkg, cls, ScreenProfile.UNKNOWN, "");
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

        while (!q.isEmpty() && visited < 180 && out.length() < 4200) {
            AccessibilityNodeInfo node = q.removeFirst();
            visited++;
            CharSequence nodeText = node.getText();
            CharSequence nodeDesc = node.getContentDescription();
            append(out, nodeText);
            append(out, nodeDesc);
            CharSequence selectedLabel = nodeText != null ? nodeText : nodeDesc;
            if ((node.isSelected() || node.isChecked() || node.isFocused()) && selectedLabel != null) {
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
        if (sample.length() > 650) sample = sample.substring(0, 650);
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
    @Override public void onDestroy() { hide(); super.onDestroy(); }
}
