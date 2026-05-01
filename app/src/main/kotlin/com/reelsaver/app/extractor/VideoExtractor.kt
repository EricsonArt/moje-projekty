package com.reelsaver.app.extractor

import com.reelsaver.app.data.Settings
import okhttp3.OkHttpClient
import okhttp3.Request
import org.json.JSONArray
import org.json.JSONObject
import java.io.IOException
import java.math.BigInteger
import java.util.concurrent.TimeUnit

data class VideoMeta(
    val downloadUrl: String,
    val sourceHost: SourceHost,
    val authorHandle: String?,
    val shortcode: String?,
    val refererUrl: String? = null
)

enum class SourceHost { INSTAGRAM, TIKTOK }

object VideoExtractor {

    private const val WEB_UA =
        "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 " +
                "(KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"

    private const val IG_WEB_APP_ID = "936619743392459"
    private const val IG_BASE64URL =
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"

    private val client: OkHttpClient = OkHttpClient.Builder()
        .connectTimeout(15, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .followRedirects(true)
        .build()

    @Throws(IOException::class)
    fun extract(pageUrl: String, settings: Settings): VideoMeta {
        val normalized = normalize(pageUrl)
        val host = detectHost(normalized)
            ?: throw IOException("Nieobsługiwany serwis: $normalized")
        return when (host) {
            SourceHost.INSTAGRAM -> extractInstagram(normalized, settings)
            SourceHost.TIKTOK -> extractTikTok(normalized)
        }
    }

    private fun normalize(url: String): String =
        url.trim().substringBefore(" ").substringBefore("?")

    private fun detectHost(url: String): SourceHost? = when {
        url.contains("instagram.com") -> SourceHost.INSTAGRAM
        url.contains("tiktok.com") -> SourceHost.TIKTOK
        else -> null
    }

    // ---------------- Instagram ----------------

    private fun extractInstagram(url: String, settings: Settings): VideoMeta {
        val shortcode = INSTAGRAM_SHORTCODE.find(url)?.groupValues?.get(1)
            ?: throw IOException("Niepoprawny link Instagrama (brak shortcode).")

        val cookies = settings.igCookies
        if (!cookies.isNullOrBlank()) {
            try {
                return fetchViaInstagramApi(shortcode, cookies)
            } catch (e: IOException) {
                // fall through to public
            }
        }
        return fetchInstagramPublicHtml(url, shortcode)
    }

    private fun fetchViaInstagramApi(shortcode: String, cookies: String): VideoMeta {
        val mediaId = shortcodeToMediaId(shortcode)
        val apiUrl = "https://i.instagram.com/api/v1/media/$mediaId/info/"
        val req = Request.Builder()
            .url(apiUrl)
            .header("User-Agent", WEB_UA)
            .header("X-IG-App-ID", IG_WEB_APP_ID)
            .header("Cookie", cookies)
            .header("Accept", "application/json")
            .header("Accept-Language", "en-US,en;q=0.9")
            .header("Referer", "https://www.instagram.com/")
            .build()
        client.newCall(req).execute().use { resp ->
            if (!resp.isSuccessful) {
                throw IOException(
                    "Instagram API HTTP ${resp.code} — sesja wygasła? Zaloguj się ponownie."
                )
            }
            val body = resp.body?.string()
                ?: throw IOException("Pusta odpowiedź API Instagrama.")
            val root = JSONObject(body)
            val items = root.optJSONArray("items")
                ?: throw IOException("Instagram API: brak \"items\".")
            if (items.length() == 0) throw IOException("Instagram API: \"items\" puste.")
            val item = items.getJSONObject(0)

            val author = item.optJSONObject("user")?.optString("username")
            val videoUrl = pickVideoUrlFromIgItem(item)
                ?: throw IOException("Brak filmu w odpowiedzi (post bez wideo?).")
            return VideoMeta(
                downloadUrl = videoUrl,
                sourceHost = SourceHost.INSTAGRAM,
                authorHandle = author,
                shortcode = shortcode,
                refererUrl = "https://www.instagram.com/"
            )
        }
    }

    private fun pickVideoUrlFromIgItem(item: JSONObject): String? {
        item.optJSONArray("video_versions")?.let { return pickHighest(it) }
        item.optJSONArray("carousel_media")?.let { car ->
            for (i in 0 until car.length()) {
                val child = car.getJSONObject(i)
                child.optJSONArray("video_versions")?.let { return pickHighest(it) }
            }
        }
        return null
    }

    private fun pickHighest(versions: JSONArray): String? {
        var bestUrl: String? = null
        var bestArea = -1
        for (i in 0 until versions.length()) {
            val v = versions.getJSONObject(i)
            val w = v.optInt("width", 0)
            val h = v.optInt("height", 0)
            val area = w * h
            val url = v.optString("url").takeIf { it.isNotBlank() } ?: continue
            if (area > bestArea) { bestArea = area; bestUrl = url }
        }
        return bestUrl
    }

    private fun fetchInstagramPublicHtml(url: String, shortcode: String): VideoMeta {
        val html = fetchHtml(url, null)
        val ogVideo = META_OG_VIDEO.find(html)?.groupValues?.get(1)?.let(::decodeHtmlEntities)
        if (!ogVideo.isNullOrBlank()) {
            val author = META_AUTHOR.find(html)?.groupValues?.get(1)
            return VideoMeta(ogVideo, SourceHost.INSTAGRAM, author, shortcode,
                refererUrl = "https://www.instagram.com/")
        }
        val jsonVideo = JSON_VIDEO_URL.find(html)?.groupValues?.get(1)?.let(::unescapeJson)
        if (!jsonVideo.isNullOrBlank()) {
            return VideoMeta(jsonVideo, SourceHost.INSTAGRAM, null, shortcode,
                refererUrl = "https://www.instagram.com/")
        }
        throw IOException(
            "Nie udało się pobrać linku publicznie. Zaloguj się do Instagrama w aplikacji."
        )
    }

    private fun shortcodeToMediaId(shortcode: String): String {
        var id = BigInteger.ZERO
        val base = BigInteger.valueOf(64)
        for (c in shortcode) {
            val idx = IG_BASE64URL.indexOf(c)
            if (idx < 0) throw IOException("Nieprawidłowy znak w shortcode: $c")
            id = id.multiply(base).add(BigInteger.valueOf(idx.toLong()))
        }
        return id.toString()
    }

    // ---------------- TikTok ----------------

    private fun extractTikTok(url: String): VideoMeta {
        val resolved = if (url.contains("/t/") || url.contains("vm.tiktok") || url.contains("vt.tiktok")) {
            resolveRedirect(url)
        } else url

        val html = fetchHtml(resolved, null)
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

        return VideoMeta(
            downloadUrl = playUrl,
            sourceHost = SourceHost.TIKTOK,
            authorHandle = author,
            shortcode = videoId,
            refererUrl = "https://www.tiktok.com/"
        )
    }

    // ---------------- Common helpers ----------------

    private fun resolveRedirect(url: String): String {
        val req = Request.Builder()
            .url(url)
            .header("User-Agent", WEB_UA)
            .head()
            .build()
        client.newCall(req).execute().use { resp -> return resp.request.url.toString() }
    }

    private fun fetchHtml(url: String, cookies: String?): String {
        val builder = Request.Builder()
            .url(url)
            .header("User-Agent", WEB_UA)
            .header("Accept-Language", "en-US,en;q=0.9")
        if (!cookies.isNullOrBlank()) builder.header("Cookie", cookies)
        client.newCall(builder.build()).execute().use { resp ->
            if (!resp.isSuccessful) throw IOException("HTTP ${resp.code} dla $url")
            return resp.body?.string() ?: throw IOException("Pusta odpowiedź dla $url")
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

    private val INSTAGRAM_SHORTCODE = Regex("""instagram\.com/(?:reel|p|tv|reels)/([A-Za-z0-9_-]+)""")
    private val META_OG_VIDEO =
        Regex("""<meta\s+property=["']og:video["']\s+content=["']([^"']+)["']""")
    private val META_AUTHOR =
        Regex("""<meta\s+name=["']author["']\s+content=["']([^"']+)["']""")
    private val JSON_VIDEO_URL = Regex(""""video_url":"([^"]+)"""")
    private val TIKTOK_REHYDRATION = Regex(
        """<script[^>]*id=["']__UNIVERSAL_DATA_FOR_REHYDRATION__["'][^>]*>(.*?)</script>""",
        RegexOption.DOT_MATCHES_ALL
    )
}
