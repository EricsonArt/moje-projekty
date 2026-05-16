package com.reelsaver.app

import android.os.Bundle
import android.view.View
import android.webkit.CookieManager
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.FrameLayout
import android.widget.TextView
import android.widget.Toast
import androidx.activity.ComponentActivity
import com.reelsaver.app.data.Settings

class InstagramLoginActivity : ComponentActivity() {

    private lateinit var settings: Settings
    private lateinit var webView: WebView
    private lateinit var statusBar: TextView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        settings = Settings(this)

        val container = FrameLayout(this)
        webView = WebView(this).also { container.addView(it) }
        statusBar = TextView(this).apply {
            text = getString(R.string.ig_login_hint)
            setPadding(24, 16, 24, 16)
            setBackgroundColor(0xCC000000.toInt())
            setTextColor(0xFFFFFFFF.toInt())
        }
        val statusParams = FrameLayout.LayoutParams(
            FrameLayout.LayoutParams.MATCH_PARENT,
            FrameLayout.LayoutParams.WRAP_CONTENT
        )
        container.addView(statusBar, statusParams)
        setContentView(container)

        with(webView.settings) {
            javaScriptEnabled = true
            domStorageEnabled = true
            userAgentString =
                "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 " +
                        "(KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"
        }

        CookieManager.getInstance().also {
            it.setAcceptCookie(true)
            it.setAcceptThirdPartyCookies(webView, true)
            it.removeAllCookies(null)
            it.flush()
        }

        webView.webViewClient = object : WebViewClient() {
            override fun onPageFinished(view: WebView?, url: String?) {
                if (url == null) return
                tryCapture(url)
            }
        }

        webView.loadUrl("https://www.instagram.com/accounts/login/")
    }

    private fun tryCapture(currentUrl: String) {
        val cookies = CookieManager.getInstance().getCookie("https://www.instagram.com/") ?: return
        val parsed = parseCookies(cookies)
        val sessionId = parsed["sessionid"]
        val dsUserId = parsed["ds_user_id"]
        if (sessionId.isNullOrBlank() || dsUserId.isNullOrBlank()) return

        val onLoginPage = currentUrl.contains("/accounts/login") ||
                currentUrl.contains("/challenge") ||
                currentUrl.contains("/two_factor")
        if (onLoginPage) {
            statusBar.text = getString(R.string.ig_login_hint_done_almost)
            return
        }

        settings.igCookies = cookies
        webView.evaluateJavascript(
            "document.cookie + '|||' + (window._sharedData?.config?.viewer?.username || '')"
        ) { _ -> /* fallback below */ }

        val username = USERNAME_FROM_COOKIE.find(cookies)?.groupValues?.get(1)
        if (!username.isNullOrBlank()) settings.igUsername = username

        statusBar.text = getString(R.string.ig_login_hint_done)
        statusBar.postDelayed({
            Toast.makeText(this, R.string.ig_login_done_toast, Toast.LENGTH_LONG).show()
            finish()
        }, 800)
        statusBar.visibility = View.VISIBLE
    }

    private fun parseCookies(raw: String): Map<String, String> =
        raw.split(";").mapNotNull { part ->
            val kv = part.trim().split("=", limit = 2)
            if (kv.size == 2) kv[0] to kv[1] else null
        }.toMap()

    @Suppress("OVERRIDE_DEPRECATION", "DEPRECATION")
    override fun onBackPressed() {
        if (webView.canGoBack()) webView.goBack() else super.onBackPressed()
    }

    companion object {
        private val USERNAME_FROM_COOKIE = Regex("""(?:^|;\s*)ds_user=([^;]+)""")
    }
}
