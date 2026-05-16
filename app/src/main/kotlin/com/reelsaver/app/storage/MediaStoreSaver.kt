package com.reelsaver.app.storage

import android.content.ContentValues
import android.content.Context
import android.net.Uri
import android.os.Build
import android.os.Environment
import android.provider.MediaStore
import com.reelsaver.app.extractor.SourceHost
import com.reelsaver.app.extractor.VideoMeta
import java.io.File
import java.io.IOException

object MediaStoreSaver {

    @Throws(IOException::class)
    fun saveVideoFromFile(context: Context, source: File, meta: VideoMeta): Uri {
        val resolver = context.contentResolver
        val displayName = buildVideoFileName(meta)
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
            ?: throw IOException("MediaStore odrzucił wpis (wideo).")

        try {
            resolver.openOutputStream(itemUri)?.use { out ->
                source.inputStream().use { input -> input.copyTo(out) }
            } ?: throw IOException("Nie udało się otworzyć strumienia zapisu (wideo).")

            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                val finalize = ContentValues().apply { put(MediaStore.Video.Media.IS_PENDING, 0) }
                resolver.update(itemUri, finalize, null, null)
            }
            return itemUri
        } catch (t: Throwable) {
            runCatching { resolver.delete(itemUri, null, null) }
            throw t
        }
    }

    @Throws(IOException::class)
    fun saveTranscript(context: Context, content: String, meta: VideoMeta): Uri {
        val resolver = context.contentResolver
        val baseName = buildVideoFileName(meta).removeSuffix(".mp4")
        val displayName = "$baseName.txt"

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            val values = ContentValues().apply {
                put(MediaStore.MediaColumns.DISPLAY_NAME, displayName)
                put(MediaStore.MediaColumns.MIME_TYPE, "text/plain")
                put(MediaStore.MediaColumns.RELATIVE_PATH,
                    Environment.DIRECTORY_DOCUMENTS + "/ReelSaver")
                put(MediaStore.MediaColumns.IS_PENDING, 1)
            }
            val collection =
                MediaStore.Files.getContentUri(MediaStore.VOLUME_EXTERNAL_PRIMARY)
            val itemUri = resolver.insert(collection, values)
                ?: throw IOException("MediaStore odrzucił wpis (transkrypcja).")
            try {
                resolver.openOutputStream(itemUri)?.use { it.write(content.toByteArray(Charsets.UTF_8)) }
                    ?: throw IOException("Nie udało się otworzyć strumienia (transkrypcja).")
                val finalize = ContentValues().apply { put(MediaStore.MediaColumns.IS_PENDING, 0) }
                resolver.update(itemUri, finalize, null, null)
                return itemUri
            } catch (t: Throwable) {
                runCatching { resolver.delete(itemUri, null, null) }
                throw t
            }
        } else {
            val docs = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOCUMENTS)
            val dir = File(docs, "ReelSaver").apply { mkdirs() }
            val out = File(dir, displayName)
            out.writeText(content, Charsets.UTF_8)
            return Uri.fromFile(out)
        }
    }

    private fun buildVideoFileName(meta: VideoMeta): String {
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
