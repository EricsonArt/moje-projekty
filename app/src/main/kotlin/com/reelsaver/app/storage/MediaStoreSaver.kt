package com.reelsaver.app.storage

import android.content.ContentValues
import android.content.Context
import android.net.Uri
import android.os.Build
import android.os.Environment
import android.provider.MediaStore
import com.reelsaver.app.extractor.SourceHost
import com.reelsaver.app.extractor.VideoMeta
import okhttp3.OkHttpClient
import okhttp3.Request
import java.io.IOException
import java.io.OutputStream
import java.util.concurrent.TimeUnit

object MediaStoreSaver {

    private const val UA =
        "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 " +
        "(KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"

    private val client: OkHttpClient = OkHttpClient.Builder()
        .connectTimeout(15, TimeUnit.SECONDS)
        .readTimeout(60, TimeUnit.SECONDS)
        .followRedirects(true)
        .build()

    @Throws(IOException::class)
    fun saveVideo(
        context: Context,
        meta: VideoMeta,
        onProgress: (bytesRead: Long, totalBytes: Long) -> Unit
    ): Uri {
        val resolver = context.contentResolver
        val displayName = buildFileName(meta)
        val relativePath = Environment.DIRECTORY_MOVIES + "/ReelSaver"

        val values = ContentValues().apply {
            put(MediaStore.Video.Media.DISPLAY_NAME, displayName)
            put(MediaStore.Video.Media.MIME_TYPE, "video/mp4")
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                put(MediaStore.Video.Media.RELATIVE_PATH, relativePath)
                put(MediaStore.Video.Media.IS_PENDING, 1)
            }
        }

        val collection = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            MediaStore.Video.Media.getContentUri(MediaStore.VOLUME_EXTERNAL_PRIMARY)
        } else {
            MediaStore.Video.Media.EXTERNAL_CONTENT_URI
        }

        val itemUri = resolver.insert(collection, values)
            ?: throw IOException("MediaStore odrzucił wpis.")

        try {
            resolver.openOutputStream(itemUri)?.use { out ->
                downloadTo(meta.downloadUrl, out, onProgress)
            } ?: throw IOException("Nie udało się otworzyć strumienia zapisu.")

            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                val finalize = ContentValues().apply {
                    put(MediaStore.Video.Media.IS_PENDING, 0)
                }
                resolver.update(itemUri, finalize, null, null)
            }
            return itemUri
        } catch (t: Throwable) {
            runCatching { resolver.delete(itemUri, null, null) }
            throw t
        }
    }

    private fun downloadTo(
        url: String,
        out: OutputStream,
        onProgress: (Long, Long) -> Unit
    ) {
        val req = Request.Builder()
            .url(url)
            .header("User-Agent", UA)
            .header("Referer", "https://www.instagram.com/")
            .build()

        client.newCall(req).execute().use { resp ->
            if (!resp.isSuccessful) {
                throw IOException("HTTP ${resp.code} przy pobieraniu pliku.")
            }
            val body = resp.body ?: throw IOException("Pusta odpowiedź pliku.")
            val total = body.contentLength()
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

    private fun buildFileName(meta: VideoMeta): String {
        val prefix = when (meta.sourceHost) {
            SourceHost.INSTAGRAM -> "ig"
            SourceHost.TIKTOK -> "tt"
        }
        val author = meta.authorHandle?.replace(Regex("[^A-Za-z0-9_]"), "")?.take(24)
        val id = meta.shortcode?.replace(Regex("[^A-Za-z0-9_-]"), "")?.take(24)
        val parts = listOfNotNull(prefix, author, id, System.currentTimeMillis().toString())
        return parts.joinToString("_") + ".mp4"
    }
}
