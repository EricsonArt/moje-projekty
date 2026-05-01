package com.reelsaver.app.storage

import okhttp3.OkHttpClient
import okhttp3.Request
import java.io.File
import java.io.IOException
import java.util.concurrent.TimeUnit

object Downloader {

    private const val UA =
        "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 " +
                "(KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"

    private val client: OkHttpClient = OkHttpClient.Builder()
        .connectTimeout(15, TimeUnit.SECONDS)
        .readTimeout(60, TimeUnit.SECONDS)
        .followRedirects(true)
        .build()

    @Throws(IOException::class)
    fun download(
        url: String,
        dst: File,
        referer: String?,
        onProgress: (bytesRead: Long, totalBytes: Long) -> Unit
    ) {
        val builder = Request.Builder()
            .url(url)
            .header("User-Agent", UA)
        if (!referer.isNullOrBlank()) builder.header("Referer", referer)

        client.newCall(builder.build()).execute().use { resp ->
            if (!resp.isSuccessful) {
                throw IOException("HTTP ${resp.code} przy pobieraniu pliku.")
            }
            val body = resp.body ?: throw IOException("Pusta odpowiedź pliku.")
            val total = body.contentLength()
            dst.parentFile?.mkdirs()
            dst.outputStream().use { out ->
                body.byteStream().use { input ->
                    val buffer = ByteArray(64 * 1024)
                    var read: Int
                    var done = 0L
                    while (input.read(buffer).also { read = it } != -1) {
                        out.write(buffer, 0, read)
                        done += read
                        onProgress(done, total)
                    }
                    out.flush()
                }
            }
        }
    }
}
