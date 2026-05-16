package com.reelsaver.app.data

import android.content.Context
import androidx.core.content.edit

enum class IgMode { PUBLIC_WEB, LOGGED_IN }

class Settings(context: Context) {

    private val prefs = context.applicationContext
        .getSharedPreferences("reelsaver", Context.MODE_PRIVATE)

    var openAiApiKey: String?
        get() = prefs.getString(KEY_OPENAI, null)?.takeIf { it.isNotBlank() }
        set(v) = prefs.edit { if (v.isNullOrBlank()) remove(KEY_OPENAI) else putString(KEY_OPENAI, v) }

    var targetLanguage: String
        get() = prefs.getString(KEY_TARGET_LANG, "pl") ?: "pl"
        set(v) = prefs.edit { putString(KEY_TARGET_LANG, v) }

    var autoTranscribe: Boolean
        get() = prefs.getBoolean(KEY_AUTO_TRANSCRIBE, false)
        set(v) = prefs.edit { putBoolean(KEY_AUTO_TRANSCRIBE, v) }

    var igCookies: String?
        get() = prefs.getString(KEY_IG_COOKIES, null)?.takeIf { it.isNotBlank() }
        set(v) = prefs.edit { if (v.isNullOrBlank()) remove(KEY_IG_COOKIES) else putString(KEY_IG_COOKIES, v) }

    var igUsername: String?
        get() = prefs.getString(KEY_IG_USERNAME, null)?.takeIf { it.isNotBlank() }
        set(v) = prefs.edit { if (v.isNullOrBlank()) remove(KEY_IG_USERNAME) else putString(KEY_IG_USERNAME, v) }

    var igMode: IgMode
        get() = IgMode.entries.firstOrNull { it.name == prefs.getString(KEY_IG_MODE, null) }
            ?: IgMode.PUBLIC_WEB
        set(v) = prefs.edit { putString(KEY_IG_MODE, v.name) }

    fun clearInstagramSession() {
        prefs.edit {
            remove(KEY_IG_COOKIES)
            remove(KEY_IG_USERNAME)
        }
    }

    companion object {
        private const val KEY_OPENAI = "openai_key"
        private const val KEY_TARGET_LANG = "target_lang"
        private const val KEY_AUTO_TRANSCRIBE = "auto_transcribe"
        private const val KEY_IG_COOKIES = "ig_cookies"
        private const val KEY_IG_USERNAME = "ig_username"
        private const val KEY_IG_MODE = "ig_mode"

        val SUPPORTED_LANGUAGES = linkedMapOf(
            "pl" to "Polski",
            "en" to "Angielski",
            "de" to "Niemiecki",
            "es" to "Hiszpański",
            "fr" to "Francuski",
            "it" to "Włoski",
            "uk" to "Ukraiński",
            "ru" to "Rosyjski",
            "cs" to "Czeski",
            "pt" to "Portugalski",
            "tr" to "Turecki",
            "nl" to "Niderlandzki"
        )
    }
}
