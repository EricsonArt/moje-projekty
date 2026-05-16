package com.reelsaver.app.transcribe

import okhttp3.MediaType.Companion.toMediaType
import okhttp3.MultipartBody
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.asRequestBody
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.io.IOException
import java.util.concurrent.TimeUnit

class TranscriptionApi(private val apiKey: String) {

    private val client: OkHttpClient = OkHttpClient.Builder()
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(180, TimeUnit.SECONDS)
        .writeTimeout(180, TimeUnit.SECONDS)
        .build()

    data class Transcript(val text: String, val detectedLanguage: String?)

    /**
     * Sends file to OpenAI Whisper. File must be <= 25 MB.
     * Returns plain text + ISO-639-1 detected language code (when verbose_json works).
     */
    @Throws(IOException::class)
    fun transcribe(file: File): Transcript {
        if (!file.exists()) throw IOException("Plik audio/video nie istnieje: ${file.path}")
        if (file.length() > MAX_BYTES) {
            throw IOException(
                "Plik ma ${file.length() / 1024 / 1024} MB — limit Whisper API to 25 MB."
            )
        }
        val body = MultipartBody.Builder()
            .setType(MultipartBody.FORM)
            .addFormDataPart(
                "file", file.name,
                file.asRequestBody("video/mp4".toMediaType())
            )
            .addFormDataPart("model", "whisper-1")
            .addFormDataPart("response_format", "verbose_json")
            .build()
        val req = Request.Builder()
            .url("https://api.openai.com/v1/audio/transcriptions")
            .header("Authorization", "Bearer $apiKey")
            .post(body)
            .build()
        client.newCall(req).execute().use { resp ->
            val raw = resp.body?.string().orEmpty()
            if (!resp.isSuccessful) {
                throw IOException("Whisper API HTTP ${resp.code}: ${raw.take(200)}")
            }
            val json = JSONObject(raw)
            val text = json.optString("text").trim()
            val lang = json.optString("language").takeIf { it.isNotBlank() }
            return Transcript(text, lang)
        }
    }

    /**
     * Translates `text` to [targetLangCode] (ISO-639-1, e.g. "pl") using gpt-4o-mini.
     * If `detected` matches target, returns input unchanged.
     */
    @Throws(IOException::class)
    fun translate(text: String, targetLangCode: String, detected: String?): String {
        if (text.isBlank()) return text
        if (detected != null && languageMatches(detected, targetLangCode)) return text
        val targetName = LANG_NAMES[targetLangCode.lowercase()] ?: targetLangCode
        val systemMsg =
            "You are a translation engine. Translate the user's text into $targetName " +
                    "($targetLangCode). Preserve line breaks and punctuation. " +
                    "Output only the translation, no preamble, no notes."
        val payload = JSONObject().apply {
            put("model", "gpt-4o-mini")
            put("temperature", 0)
            put("messages", JSONArray().apply {
                put(JSONObject().put("role", "system").put("content", systemMsg))
                put(JSONObject().put("role", "user").put("content", text))
            })
        }.toString().toRequestBody("application/json".toMediaType())
        val req = Request.Builder()
            .url("https://api.openai.com/v1/chat/completions")
            .header("Authorization", "Bearer $apiKey")
            .post(payload)
            .build()
        client.newCall(req).execute().use { resp ->
            val raw = resp.body?.string().orEmpty()
            if (!resp.isSuccessful) {
                throw IOException("Translate API HTTP ${resp.code}: ${raw.take(200)}")
            }
            val json = JSONObject(raw)
            return json.getJSONArray("choices").getJSONObject(0)
                .getJSONObject("message").getString("content").trim()
        }
    }

    private fun languageMatches(detected: String, target: String): Boolean {
        val d = detected.lowercase()
        val t = target.lowercase()
        if (d == t) return true
        val tName = LANG_NAMES[t]
        if (tName != null && d == tName.lowercase()) return true
        val dCode = LANG_NAMES.entries.firstOrNull { it.value.equals(d, true) }?.key
        return dCode == t
    }

    companion object {
        private const val MAX_BYTES = 25L * 1024L * 1024L
        private val LANG_NAMES = mapOf(
            "pl" to "Polish", "en" to "English", "de" to "German",
            "es" to "Spanish", "fr" to "French", "it" to "Italian",
            "uk" to "Ukrainian", "ru" to "Russian", "cs" to "Czech",
            "pt" to "Portuguese", "tr" to "Turkish", "nl" to "Dutch"
        )
    }
}
