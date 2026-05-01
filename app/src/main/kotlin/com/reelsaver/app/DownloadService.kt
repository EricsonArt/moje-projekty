package com.reelsaver.app

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.content.pm.ServiceInfo
import android.net.Uri
import android.os.Build
import androidx.core.app.NotificationCompat
import androidx.lifecycle.LifecycleService
import androidx.lifecycle.lifecycleScope
import com.reelsaver.app.extractor.VideoExtractor
import com.reelsaver.app.storage.MediaStoreSaver
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.util.concurrent.atomic.AtomicInteger

class DownloadService : LifecycleService() {

    private val nextJobId = AtomicInteger(1000)

    override fun onCreate() {
        super.onCreate()
        ensureChannels()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        super.onStartCommand(intent, flags, startId)
        val url = intent?.getStringExtra(EXTRA_URL)
        if (url.isNullOrBlank()) {
            stopSelfSafely(startId)
            return START_NOT_STICKY
        }
        val jobId = nextJobId.getAndIncrement()
        startForegroundForJob(jobId, getString(R.string.notif_starting))
        lifecycleScope.launch { runJob(jobId, url, startId) }
        return START_NOT_STICKY
    }

    private suspend fun runJob(jobId: Int, url: String, startId: Int) {
        try {
            updateProgressNotification(jobId, getString(R.string.notif_extracting), null)
            val meta = withContext(Dispatchers.IO) { VideoExtractor.extract(url) }

            updateProgressNotification(jobId, getString(R.string.notif_downloading), 0)
            val savedUri = withContext(Dispatchers.IO) {
                MediaStoreSaver.saveVideo(this@DownloadService, meta) { read, total ->
                    val pct = if (total > 0) ((read * 100) / total).toInt() else null
                    updateProgressNotification(jobId, getString(R.string.notif_downloading), pct)
                }
            }
            postDoneNotification(jobId, savedUri)
        } catch (t: Throwable) {
            postErrorNotification(jobId, t.message ?: t::class.java.simpleName)
        } finally {
            stopSelfSafely(startId)
        }
    }

    private fun startForegroundForJob(jobId: Int, text: String) {
        val notif = baseBuilder(text)
            .setProgress(0, 0, true)
            .build()
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.UPSIDE_DOWN_CAKE) {
            startForeground(FOREGROUND_NOTIF_ID, notif, ServiceInfo.FOREGROUND_SERVICE_TYPE_DATA_SYNC)
        } else {
            startForeground(FOREGROUND_NOTIF_ID, notif)
        }
    }

    private fun updateProgressNotification(jobId: Int, text: String, percent: Int?) {
        val builder = baseBuilder(text)
        if (percent == null) builder.setProgress(0, 0, true)
        else builder.setProgress(100, percent, false)
        notificationManager().notify(FOREGROUND_NOTIF_ID, builder.build())
    }

    private fun postDoneNotification(jobId: Int, fileUri: Uri) {
        val openIntent = Intent(Intent.ACTION_VIEW).apply {
            setDataAndType(fileUri, "video/mp4")
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }
        val pi = PendingIntent.getActivity(
            this, fileUri.hashCode(), openIntent,
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
        )
        val notif = NotificationCompat.Builder(this, CHANNEL_DONE)
            .setSmallIcon(android.R.drawable.stat_sys_download_done)
            .setContentTitle(getString(R.string.notif_done_title))
            .setContentText(getString(R.string.notif_done_text))
            .setContentIntent(pi)
            .setAutoCancel(true)
            .build()
        notificationManager().notify(jobId, notif)
    }

    private fun postErrorNotification(jobId: Int, message: String) {
        val notif = NotificationCompat.Builder(this, CHANNEL_DONE)
            .setSmallIcon(android.R.drawable.stat_notify_error)
            .setContentTitle(getString(R.string.notif_error_title))
            .setContentText(message)
            .setStyle(NotificationCompat.BigTextStyle().bigText(message))
            .setAutoCancel(true)
            .build()
        notificationManager().notify(jobId, notif)
    }

    private fun baseBuilder(text: String): NotificationCompat.Builder =
        NotificationCompat.Builder(this, CHANNEL_PROGRESS)
            .setSmallIcon(android.R.drawable.stat_sys_download)
            .setContentTitle(getString(R.string.notif_progress_title))
            .setContentText(text)
            .setOngoing(true)
            .setOnlyAlertOnce(true)

    private fun stopSelfSafely(startId: Int) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
            stopForeground(STOP_FOREGROUND_REMOVE)
        } else {
            @Suppress("DEPRECATION")
            stopForeground(true)
        }
        stopSelf(startId)
    }

    private fun ensureChannels() {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) return
        val mgr = notificationManager()
        if (mgr.getNotificationChannel(CHANNEL_PROGRESS) == null) {
            mgr.createNotificationChannel(
                NotificationChannel(
                    CHANNEL_PROGRESS,
                    getString(R.string.channel_progress),
                    NotificationManager.IMPORTANCE_LOW
                )
            )
        }
        if (mgr.getNotificationChannel(CHANNEL_DONE) == null) {
            mgr.createNotificationChannel(
                NotificationChannel(
                    CHANNEL_DONE,
                    getString(R.string.channel_done),
                    NotificationManager.IMPORTANCE_DEFAULT
                )
            )
        }
    }

    private fun notificationManager(): NotificationManager =
        getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager

    companion object {
        const val EXTRA_URL = "extra_url"
        private const val FOREGROUND_NOTIF_ID = 1
        private const val CHANNEL_PROGRESS = "reelsaver.progress"
        private const val CHANNEL_DONE = "reelsaver.done"
    }
}
