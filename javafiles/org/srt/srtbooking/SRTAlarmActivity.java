package org.srt.srtbooking;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.os.Build;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

/**
 * 예매 완료 / IP 차단 감지 시 표시되는 전용 알람 팝업.
 * 잠금화면 위에 전체화면으로 표시됩니다.
 */
public class SRTAlarmActivity extends Activity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // ── 잠금화면 위에 표시 (잠금 해제 없이) ─────────────
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O_MR1) {   // API 27+
            setShowWhenLocked(true);
            setTurnScreenOn(true);
        } else {
            getWindow().addFlags(
                WindowManager.LayoutParams.FLAG_SHOW_WHEN_LOCKED |
                WindowManager.LayoutParams.FLAG_TURN_SCREEN_ON   |
                WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON
            );
        }

        String title   = getIntent().getStringExtra("title");
        String message = getIntent().getStringExtra("message");
        boolean isSuccess = getIntent().getBooleanExtra("is_success", false);

        int bgColor      = isSuccess ? Color.parseColor("#0D2137") : Color.parseColor("#2D1010");
        int accentColor  = isSuccess ? Color.parseColor("#4CAF50") : Color.parseColor("#F44336");
        int btnColor     = isSuccess ? Color.parseColor("#1976D2") : Color.parseColor("#B71C1C");

        // ── 레이아웃 ─────────────────────────────────────────
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setGravity(Gravity.CENTER);
        root.setBackgroundColor(bgColor);
        root.setPadding(60, 80, 60, 80);

        // 이모지 + 제목
        TextView tvTitle = new TextView(this);
        tvTitle.setText(title != null ? title : "SRT 알림");
        tvTitle.setTextColor(Color.WHITE);
        tvTitle.setTextSize(28f);
        tvTitle.setTypeface(null, Typeface.BOLD);
        tvTitle.setGravity(Gravity.CENTER);
        tvTitle.setPadding(0, 0, 0, 32);

        // 구분선
        View divider = new View(this);
        divider.setBackgroundColor(accentColor);
        LinearLayout.LayoutParams divLP = new LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.MATCH_PARENT, 3);
        divLP.setMargins(0, 0, 0, 40);

        // 메시지
        TextView tvMsg = new TextView(this);
        tvMsg.setText(message != null ? message : "");
        tvMsg.setTextColor(Color.parseColor("#DDDDDD"));
        tvMsg.setTextSize(16f);
        tvMsg.setGravity(Gravity.CENTER);
        tvMsg.setPadding(0, 0, 0, 60);
        tvMsg.setLineSpacing(8f, 1f);

        // 확인 버튼
        Button btnOk = new Button(this);
        btnOk.setText("확 인");
        btnOk.setTextColor(Color.WHITE);
        btnOk.setTextSize(18f);
        btnOk.setTypeface(null, Typeface.BOLD);
        btnOk.setBackgroundColor(btnColor);
        LinearLayout.LayoutParams btnLP = new LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.MATCH_PARENT,
            LinearLayout.LayoutParams.WRAP_CONTENT);
        btnLP.setMargins(0, 0, 0, 0);
        btnOk.setLayoutParams(btnLP);
        btnOk.setPadding(0, 30, 0, 30);
        btnOk.setOnClickListener(new View.OnClickListener() {
            @Override public void onClick(View v) { finish(); }
        });

        root.addView(tvTitle);
        root.addView(divider, divLP);
        root.addView(tvMsg);
        root.addView(btnOk);

        setContentView(root);
    }

    @Override
    public void onBackPressed() {
        // 백 버튼으로 닫기 허용
        finish();
    }
}
