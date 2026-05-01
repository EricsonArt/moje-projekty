package com.reelsaver.app

import android.net.Uri
import android.os.Bundle
import android.view.View
import android.webkit.WebResourceRequest
import android.webkit.WebResourceResponse
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.FrameLayout
import android.widget.TextView
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.core.content.ContextCompat
import org.json.JSONObject
import java.util.concurrent.atomic.AtomicBoolean

class WebDownloaderActivity : ComponentActivity() {

    private lateinit var webView: WebView
    private lateinit var statusBar: TextView
    private lateinit var pageUrl: String
    private val captured = AtomicBoolean(false)

    @Suppress("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        pageUrl = intent.getStringExtra(EXTRA_PAGE_URL).orEmpty()
        if (pageUrl.isBlank()) { finish(); return }

        val container = FrameLayout(this)
        webView = WebView(this).also { container.addView(it) }
        statusBar = TextView(this).apply {
            text = getString(R.string.web_dl_hint)
            setPadding(24, 16, 24, 16)
            setBackgroundColor(0xCC000000.toInt())
            setTextColor(0xFFFFFFFF.toInt())
        }
        container.addView(
            statusBar,
            FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT,
                FrameLayout.LayoutParams.WRAP_CONTENT
            )
        )
        setContentView(container)

        with(webView.settings) {
            javaScriptEnabled = true
            domStorageEnabled = true
            userAgentString =
                "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 " +
                        "(KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"
        }

        webView.setDownloadListener { url, _, _, _, _ ->
            captureMp4(url)
        }

        webView.webViewClient = object : WebViewClient() {
            override fun shouldInterceptRequest(
                view: WebView,
                request: WebResourceRequest
            ): WebResourceResponse? {
                val url = request.url.toString()
                if (looksLikeIgMp4(url)) captureMp4(url)
                return super.shouldInterceptRequest(view, request)
            }

            override fun onPageFinished(view: WebView?, url: String?) {
                if (url == null) return
                if (url.contains("snapinsta.app")) injectSnapinstaSubmit()
            }
        }

        webView.loadUrl("https://snapinsta.app/")
    }

    private fun looksLikeIgMp4(url: String): Boolean {
        if (!url.contains(".mp4", ignoreCase = true) &&
            !url.contains("video", ignoreCase = true)) return false
        val lower = url.lowercase()
        return lower.contains("cdninstagram") ||
                lower.contains("fbcdn.net") ||
                lower.contains("snapcdn") ||
                lower.contains(".mp4")
    }

    private fun injectSnapinstaSubmit() {
        val urlJson = JSONObject.quote(pageUrl)
        val js = """
            (function() {
                try {
                    var input = document.querySelector('#url') ||
                                document.querySelector('input[name="url"]') ||
                                document.querySelector('input[type="text"]');
                    if (input) {
                        input.value = $urlJson;
                        input.dispatchEvent(new Event('input', { bubbles: true }));
                        input.dispatchEvent(new Event('change', { bubbles: true }));
                    }
                    setTimeout(function() {
                        var btn = document.querySelector('#submit') ||
                                  document.querySelector('button[type="submit"]') ||
                                  document.querySelector('form button');
                        if (btn) btn.click();
                    }, 250);
                } catch (e) {}
            })();
        """.trimIndent()
        webView.evaluateJavascript(js, null)
    }

    private fun captureMp4(directUrl: String) {
        if (!captured.compareAndSet(false, true)) return
        runOnUiThread {
            statusBar.visibility = View.VISIBLE
            statusBar.text = getString(R.string.web_dl_captured)
            val svc = android.content.Intent(this, DownloadService::class.java).apply {
                putExtra(DownloadService.EXTRA_URL, pageUrl)
                putExtra(DownloadService.EXTRA_DIRECT_VIDEO_URL, directUrl)
                putExtra(DownloadService.EXTRA_REFERER, "https://snapinsta.app/")
            }
            ContextCompat.startForegroundService(this, svc)
            Toast.makeText(this, R.string.toast_started, Toast.LENGTH_SHORT).show()
            finish()
        }
    }

    @Suppress("OVERRIDE_DEPRECATION", "DEPRECATION")
    override fun onBackPressed() {
        if (webView.canGoBack()) webView.goBack() else super.onBackPressed()
    }

    companion object {
        const val EXTRA_PAGE_URL = "page_url"
    }
}
