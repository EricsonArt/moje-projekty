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
import com.reelsaver.app.data.Settings
import com.reelsaver.app.extractor.SourceHost
import com.reelsaver.app.extractor.VideoExtractor
import com.reelsaver.app.extractor.VideoMeta
import com.reelsaver.app.storage.Downloader
import com.reelsaver.app.storage.MediaStoreSaver
import com.reelsaver.app.transcribe.TranscriptionApi
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.File
import java.util.concurrent.atomic.AtomicInteger

class DownloadService : LifecycleService() {

    private val nextJobId = AtomicInteger(1000)
    private lateinit var settings: Settings

    override fun onCreate() {
        super.onCreate()
        settings = Settings(this)
        ensureChannels()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        super.onStartCommand(intent, flags, startId)
        val pageUrl = intent?.getStringExtra(EXTRA_URL)
        val directUrl = intent?.getStringExtra(EXTRA_DIRECT_VIDEO_URL)
        val referer = intent?.getStringExtra(EXTRA_REFERER)
        if (pageUrl.isNullOrBlank() && directUrl.isNullOrBlank()) {
            stopSelfSafely(startId)
            return START_NOT_STICKY
        }
        val jobId = nextJobId.getAndIncrement()
        startForegroundForJob(getString(R.string.notif_starting))
        lifecycleScope.launch { runJob(jobId, pageUrl.orEmpty(), directUrl, referer, startId) }
        return START_NOT_STICKY
    }

    private suspend fun runJob(
        jobId: Int,
        pageUrl: String,
        directUrl: String?,
        referer: String?,
        startId: Int
    ) {
        var tempFile: File? = null
        try {
            val meta: VideoMeta = if (!directUrl.isNullOrBlank()) {
                buildDirectMeta(pageUrl, directUrl, referer)
            } else {
                updateProgress(getString(R.string.notif_extracting), null)
                withContext(Dispatchers.IO) { VideoExtractor.extract(pageUrl, settings) }
            }

            updateProgress(getString(R.string.notif_downloading), 0)
            tempFile = File(cacheDir, "dl_${System.currentTimeMillis()}.mp4")
            withContext(Dispatchers.IO) {
                Downloader.download(meta.downloadUrl, tempFile, meta.refererUrl) { read, total ->
                    val pct = if (total > 0) ((read * 100) / total).toInt() else null
                    updateProgress(getString(R.string.notif_downloading), pct)
                }
            }

            updateProgress(getString(R.string.notif_saving), null)
            val savedUri = withContext(Dispatchers.IO) {
                MediaStoreSaver.saveVideoFromFile(this@DownloadService, tempFile!!, meta)
            }
            postDoneNotification(jobId, savedUri)

            if (settings.autoTranscribe) {
                runTranscription(jobId, meta, tempFile)
            }
        } catch (t: Throwable) {
            postErrorNotification(jobId, t.message ?: t::class.java.simpleName)
        } finally {
            tempFile?.delete()
            stopSelfSafely(startId)
        }
    }

    private suspend fun runTranscription(jobId: Int, meta: VideoMeta, file: File) {
        val key = settings.openAiApiKey
        if (key.isNullOrBlank()) {
            postErrorNotification(
                jobId + 1,
                getString(R.string.err_no_api_key)
            )
            return
        }
        try {
            updateProgress(getString(R.string.notif_transcribing), null)
            val api = TranscriptionApi(key)
            val transcript = withContext(Dispatchers.IO) { api.transcribe(file) }

            updateProgress(getString(R.string.notif_translating), null)
            val translated = withContext(Dispatchers.IO) {
                api.translate(transcript.text, settings.targetLanguage, transcript.detectedLanguage)
            }

            withContext(Dispatchers.IO) {
                MediaStoreSaver.saveTranscript(this@DownloadService, translated, meta)
            }
            postTranscriptNotification(jobId + 1, translated)
        } catch (t: Throwable) {
            postErrorNotification(jobId + 1, t.message ?: t::class.java.simpleName)
        }
    }

    private fun startForegroundForJob(text: String) {
        val notif = baseProgressBuilder(text).setProgress(0, 0, true).build()
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.UPSIDE_DOWN_CAKE) {
            startForeground(FOREGROUND_NOTIF_ID, notif, ServiceInfo.FOREGROUND_SERVICE_TYPE_DATA_SYNC)
        } else {
            startForeground(FOREGROUND_NOTIF_ID, notif)
        }
    }

    private fun updateProgress(text: String, percent: Int?) {
        val builder = baseProgressBuilder(text)
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

    private fun postTranscriptNotification(jobId: Int, text: String) {
        val preview = if (text.length > 600) text.take(600) + "…" else text
        val copyIntent = Intent(this, ClipboardCopyReceiver::class.java).apply {
            action = ClipboardCopyReceiver.ACTION_COPY
            putExtra(ClipboardCopyReceiver.EXTRA_TEXT, text)
        }
        val pi = PendingIntent.getBroadcast(
            this, jobId, copyIntent,
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
        )
        val notif = NotificationCompat.Builder(this, CHANNEL_DONE)
            .setSmallIcon(android.R.drawable.ic_menu_edit)
            .setContentTitle(getString(R.string.notif_transcript_title))
            .setContentText(preview.lineSequence().firstOrNull() ?: "")
            .setStyle(NotificationCompat.BigTextStyle().bigText(preview))
            .addAction(0, getString(R.string.action_copy), pi)
            .setAutoCancel(true)
            .build()
        notificationManager().notify(jobId, notif)
    }

    private fun postErrorNotification(jobId: Int, message: String) {
        val notif = NotificationCompat.Builder(this, CHANNEL_DONE)
            .setSmallIcon(android.R.drawable.stat_notify_error)
            .setContentTitle(getString(R.string.notif_error_title))
            .setContentText(message.lineSequence().firstOrNull() ?: "")
            .setStyle(NotificationCompat.BigTextStyle().bigText(message))
            .setAutoCancel(true)
            .build()
        notificationManager().notify(jobId, notif)
    }

    private fun baseProgressBuilder(text: String): NotificationCompat.Builder =
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

    private fun buildDirectMeta(pageUrl: String, directUrl: String, referer: String?): VideoMeta {
        val host = when {
            pageUrl.contains("tiktok.com") -> SourceHost.TIKTOK
            else -> SourceHost.INSTAGRAM
        }
        val shortcode = INSTAGRAM_SHORTCODE.find(pageUrl)?.groupValues?.get(1)
            ?: TIKTOK_VIDEO_ID.find(pageUrl)?.groupValues?.get(1)
        return VideoMeta(
            downloadUrl = directUrl,
            sourceHost = host,
            authorHandle = null,
            shortcode = shortcode,
            refererUrl = referer ?: when (host) {
                SourceHost.INSTAGRAM -> "https://www.instagram.com/"
                SourceHost.TIKTOK -> "https://www.tiktok.com/"
            }
        )
    }

    companion object {
        const val EXTRA_URL = "extra_url"
        const val EXTRA_DIRECT_VIDEO_URL = "extra_direct_video_url"
        const val EXTRA_REFERER = "extra_referer"
        private const val FOREGROUND_NOTIF_ID = 1
        private const val CHANNEL_PROGRESS = "reelsaver.progress"
        private const val CHANNEL_DONE = "reelsaver.done"
        private val INSTAGRAM_SHORTCODE =
            Regex("""instagram\.com/(?:reel|reels|p|tv)/([A-Za-z0-9_-]+)""")
        private val TIKTOK_VIDEO_ID = Regex("""tiktok\.com/[^/]+/video/(\d+)""")
    }
}
