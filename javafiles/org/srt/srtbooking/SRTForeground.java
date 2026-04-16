package org.srt.srtbooking;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.os.Build;
import android.os.IBinder;

/**
 * 메인 프로세스에서 실행되는 Foreground Service.
 * android:process 미지정 → 메인 앱 프로세스와 동일한 프로세스에서 실행됨.
 * startForeground() 호출로 메인 프로세스가 OS에 의해 강제 종료되지 않도록 보호.
 */
public class SRTForeground extends Service {
    static final String CHANNEL_ID = "srt_main_fg_v2";
    static final int   NOTIF_ID   = 9001;
    static final String ACTION_STOP = "STOP";

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        if (intent != null && ACTION_STOP.equals(intent.getAction())) {
            stopForeground(true);
            stopSelf();
            return START_NOT_STICKY;
        }

        NotificationManager nm =
            (NotificationManager) getSystemService(Context.NOTIFICATION_SERVICE);

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            if (nm.getNotificationChannel(CHANNEL_ID) == null) {
                NotificationChannel ch = new NotificationChannel(
                    CHANNEL_ID, "SRT 예매", NotificationManager.IMPORTANCE_MIN);
                ch.setDescription("예매 진행 중 백그라운드 보호");
                nm.createNotificationChannel(ch);
            }
        }

        Notification notif;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            notif = new Notification.Builder(this, CHANNEL_ID)
                .setContentTitle("SRT 예매 진행 중")
                .setContentText("화면이 꺼져도 예매를 계속합니다.")
                .setSmallIcon(android.R.drawable.ic_popup_sync)
                .setOngoing(true)
                .build();
        } else {
            notif = new Notification.Builder(this)
                .setContentTitle("SRT 예매 진행 중")
                .setContentText("화면이 꺼져도 예매를 계속합니다.")
                .setSmallIcon(android.R.drawable.ic_popup_sync)
                .setOngoing(true)
                .build();
        }

        startForeground(NOTIF_ID, notif);
        return START_STICKY;
    }

    @Override
    public IBinder onBind(Intent intent) { return null; }
}
