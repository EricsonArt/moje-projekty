package com.reelsaver.app

import android.content.Intent
import android.os.Build
import android.os.Bundle
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.core.content.ContextCompat
import com.reelsaver.app.data.IgMode
import com.reelsaver.app.data.Settings

class ShareReceiverActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        handleIntent(intent)
        finish()
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        handleIntent(intent)
        finish()
    }

    private fun handleIntent(intent: Intent?) {
        if (intent == null || intent.action != Intent.ACTION_SEND) return
        val text = intent.getStringExtra(Intent.EXTRA_TEXT)?.trim().orEmpty()
        val url = extractUrl(text)
        if (url == null) {
            toast(getString(R.string.toast_no_link))
            return
        }
        val settings = Settings(this)
        val isInstagram = url.contains("instagram.com")
        val usePublicWeb = isInstagram && settings.igMode == IgMode.PUBLIC_WEB

        if (usePublicWeb) {
            val webIntent = Intent(this, WebDownloaderActivity::class.java).apply {
                putExtra(WebDownloaderActivity.EXTRA_PAGE_URL, url)
                addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            }
            startActivity(webIntent)
            return
        }

        val service = Intent(this, DownloadService::class.java).apply {
            putExtra(DownloadService.EXTRA_URL, url)
        }
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            ContextCompat.startForegroundService(this, service)
        } else {
            startService(service)
        }
        toast(getString(R.string.toast_started))
    }

    private fun extractUrl(text: String): String? {
        if (text.isEmpty()) return null
        val match = URL_REGEX.find(text) ?: return null
        return match.value
    }

    private fun toast(msg: String) {
        Toast.makeText(applicationContext, msg, Toast.LENGTH_SHORT).show()
    }

    companion object {
        private val URL_REGEX = Regex("https?://\\S+")
    }
}
