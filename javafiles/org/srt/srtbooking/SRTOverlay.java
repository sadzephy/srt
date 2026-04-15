package org.srt.srtbooking;

import android.content.Context;
import android.graphics.Color;
import android.graphics.PixelFormat;
import android.graphics.Typeface;
import android.os.Build;
import android.os.Handler;
import android.os.Looper;
import android.view.Gravity;
import android.view.View;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

/**
 * SYSTEM_ALERT_WINDOW 권한을 이용한 잠금화면 위 전체화면 오버레이.
 * TYPE_APPLICATION_OVERLAY (API 26+) → 잠금화면 위에 직접 표시.
 * 삼성 알람과 동일한 원리.
 */
public class SRTOverlay {
    private static View           sView = null;
    private static WindowManager  sWm   = null;

    public static synchronized void show(Context context,
                                         String title,
                                         String message,
                                         boolean isSuccess) {
        if (sView != null) return;   // 이미 표시 중

        Context appCtx = context.getApplicationContext();
        sWm = (WindowManager) appCtx.getSystemService(Context.WINDOW_SERVICE);

        int layoutType = Build.VERSION.SDK_INT >= Build.VERSION_CODES.O
            ? WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY  // API 26+
            : WindowManager.LayoutParams.TYPE_PHONE;               // API < 26

        WindowManager.LayoutParams lp = new WindowManager.LayoutParams(
            WindowManager.LayoutParams.MATCH_PARENT,
            WindowManager.LayoutParams.MATCH_PARENT,
            layoutType,
            WindowManager.LayoutParams.FLAG_SHOW_WHEN_LOCKED |
            WindowManager.LayoutParams.FLAG_TURN_SCREEN_ON   |
            WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON,
            PixelFormat.OPAQUE
        );

        int bgColor = isSuccess ? Color.parseColor("#0D2137") : Color.parseColor("#2D1010");
        int acColor = isSuccess ? Color.parseColor("#4CAF50") : Color.parseColor("#F44336");
        int btColor = isSuccess ? Color.parseColor("#1565C0") : Color.parseColor("#B71C1C");

        LinearLayout root = new LinearLayout(appCtx);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setGravity(Gravity.CENTER);
        root.setBackgroundColor(bgColor);
        root.setPadding(60, 100, 60, 100);

        TextView tvTitle = new TextView(appCtx);
        tvTitle.setText(title != null ? title : "SRT 알림");
        tvTitle.setTextColor(Color.WHITE);
        tvTitle.setTextSize(28f);
        tvTitle.setTypeface(null, Typeface.BOLD);
        tvTitle.setGravity(Gravity.CENTER);
        tvTitle.setPadding(0, 0, 0, 24);

        View divider = new View(appCtx);
        divider.setBackgroundColor(acColor);
        LinearLayout.LayoutParams divLp = new LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.MATCH_PARENT, 3);
        divLp.setMargins(0, 0, 0, 32);

        TextView tvMsg = new TextView(appCtx);
        tvMsg.setText(message != null ? message : "");
        tvMsg.setTextColor(Color.parseColor("#DDDDDD"));
        tvMsg.setTextSize(16f);
        tvMsg.setGravity(Gravity.CENTER);
        tvMsg.setPadding(0, 0, 0, 48);
        tvMsg.setLineSpacing(8f, 1f);

        Button btnOk = new Button(appCtx);
        btnOk.setText("확 인");
        btnOk.setTextColor(Color.WHITE);
        btnOk.setTextSize(18f);
        btnOk.setTypeface(null, Typeface.BOLD);
        btnOk.setBackgroundColor(btColor);
        btnOk.setPadding(0, 30, 0, 30);
        btnOk.setOnClickListener(new View.OnClickListener() {
            @Override public void onClick(View v) { dismiss(); }
        });

        root.addView(tvTitle);
        root.addView(divider, divLp);
        root.addView(tvMsg);
        root.addView(btnOk, new LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.MATCH_PARENT,
            LinearLayout.LayoutParams.WRAP_CONTENT));

        final View finalView   = root;
        final WindowManager.LayoutParams finalLp = lp;
        sView = finalView;

        // addView()는 반드시 Android UI 스레드에서 실행
        new Handler(Looper.getMainLooper()).post(new Runnable() {
            @Override public void run() {
                try {
                    sWm.addView(finalView, finalLp);
                } catch (Exception e) {
                    sView = null;
                    sWm   = null;
                }
            }
        });
    }

    public static synchronized void dismiss() {
        if (sView != null && sWm != null) {
            try { sWm.removeView(sView); } catch (Exception ignored) {}
        }
        sView = null;
        sWm   = null;
    }
}
