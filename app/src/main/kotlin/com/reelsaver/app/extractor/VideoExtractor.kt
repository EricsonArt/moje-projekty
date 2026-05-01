package com.reelsaver.app.extractor

import okhttp3.OkHttpClient
import okhttp3.Request
import org.json.JSONObject
import java.io.IOException
import java.util.concurrent.TimeUnit

data class VideoMeta(
    val downloadUrl: String,
    val sourceHost: SourceHost,
    val authorHandle: String?,
    val shortcode: String?
)

enum class SourceHost { INSTAGRAM, TIKTOK }

object VideoExtractor {

    private const val UA =
        "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 " +
        "(KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"

    private val client: OkHttpClient = OkHttpClient.Builder()
        .connectTimeout(15, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .followRedirects(true)
        .build()

    @Throws(IOException::class)
    fun extract(pageUrl: String): VideoMeta {
        val normalized = normalize(pageUrl)
        val host = detectHost(normalized)
            ?: throw IOException("Nieobsługiwany serwis: $normalized")
        return when (host) {
            SourceHost.INSTAGRAM -> extractInstagram(normalized)
            SourceHost.TIKTOK -> extractTikTok(normalized)
        }
    }

    private fun normalize(url: String): String {
        val cleaned = url.trim().substringBefore(" ")
        return cleaned.substringBefore("?")
    }

    private fun detectHost(url: String): SourceHost? = when {
        url.contains("instagram.com") -> SourceHost.INSTAGRAM
        url.contains("tiktok.com") -> SourceHost.TIKTOK
        else -> null
    }

    private fun extractInstagram(url: String): VideoMeta {
        val shortcode = INSTAGRAM_SHORTCODE.find(url)?.groupValues?.get(1)
        val html = fetchHtml(url)

        val ogVideo = META_OG_VIDEO.find(html)?.groupValues?.get(1)?.let(::decodeHtmlEntities)
        if (!ogVideo.isNullOrBlank()) {
            val author = META_AUTHOR.find(html)?.groupValues?.get(1)
            return VideoMeta(ogVideo, SourceHost.INSTAGRAM, author, shortcode)
        }

        val jsonVideo = JSON_VIDEO_URL.find(html)?.groupValues?.get(1)?.let(::unescapeJson)
        if (!jsonVideo.isNullOrBlank()) {
            return VideoMeta(jsonVideo, SourceHost.INSTAGRAM, null, shortcode)
        }

        throw IOException(
            "Nie znaleziono URL filmu. Reel może być prywatny lub Instagram zmienił stronę."
        )
    }

    private fun extractTikTok(url: String): VideoMeta {
        val resolved = if (url.contains("/t/") || url.contains("vm.tiktok") || url.contains("vt.tiktok")) {
            resolveRedirect(url)
        } else url

        val html = fetchHtml(resolved)

        val rehydrationJson = TIKTOK_REHYDRATION.find(html)?.groupValues?.get(1)
            ?: throw IOException("TikTok: nie znaleziono danych strony.")

        val root = JSONObject(rehydrationJson)
        val itemStruct = root
            .optJSONObject("__DEFAULT_SCOPE__")
            ?.optJSONObject("webapp.video-detail")
            ?.optJSONObject("itemInfo")
            ?.optJSONObject("itemStruct")
            ?: throw IOException("TikTok: nieoczekiwana struktura odpowiedzi.")

        val video = itemStruct.optJSONObject("video")
            ?: throw IOException("TikTok: brak sekcji video.")

        val playUrl = video.optString("playAddr")
            .ifBlank { video.optString("downloadAddr") }
            .ifBlank { throw IOException("TikTok: brak URL filmu.") }

        val author = itemStruct.optJSONObject("author")?.optString("uniqueId")
        val videoId = itemStruct.optString("id").takeIf { it.isNotBlank() }

        return VideoMeta(playUrl, SourceHost.TIKTOK, author, videoId)
    }

    private fun resolveRedirect(url: String): String {
        val req = Request.Builder()
            .url(url)
            .header("User-Agent", UA)
            .head()
            .build()
        client.newCall(req).execute().use { resp ->
            return resp.request.url.toString()
        }
    }

    private fun fetchHtml(url: String): String {
        val req = Request.Builder()
            .url(url)
            .header("User-Agent", UA)
            .header("Accept-Language", "en-US,en;q=0.9")
            .build()
        client.newCall(req).execute().use { resp ->
            if (!resp.isSuccessful) {
                throw IOException("HTTP ${resp.code} dla $url")
            }
            return resp.body?.string()
                ?: throw IOException("Pusta odpowiedź dla $url")
        }
    }

    private fun decodeHtmlEntities(s: String): String =
        s.replace("&amp;", "&")
            .replace("&quot;", "\"")
            .replace("&#39;", "'")
            .replace("&lt;", "<")
            .replace("&gt;", ">")

    private fun unescapeJson(s: String): String =
        s.replace("\\u0026", "&")
            .replace("\\/", "/")
            .replace("\\\"", "\"")

    private val INSTAGRAM_SHORTCODE = Regex("""instagram\.com/(?:reel|p|tv)/([A-Za-z0-9_-]+)""")
    private val META_OG_VIDEO =
        Regex("""<meta\s+property=["']og:video["']\s+content=["']([^"']+)["']""")
    private val META_AUTHOR =
        Regex("""<meta\s+name=["']author["']\s+content=["']([^"']+)["']""")
    private val JSON_VIDEO_URL =
        Regex(""""video_url":"([^"]+)"""")
    private val TIKTOK_REHYDRATION =
        Regex(
            """<script[^>]*id=["']__UNIVERSAL_DATA_FOR_REHYDRATION__["'][^>]*>(.*?)</script>""",
            RegexOption.DOT_MATCHES_ALL
        )
}
