package com.vitalis.health.ui.components

import android.graphics.Bitmap
import android.graphics.Color as AndroidColor
import android.graphics.pdf.PdfRenderer
import android.os.ParcelFileDescriptor
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.produceState
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.unit.dp
import androidx.compose.foundation.Image
import com.vitalis.health.ui.theme.LocalVitalisColors
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.File

@Composable
fun PdfRendererViewer(
    pdfFile: File,
    pageCount: Int,
    modifier: Modifier = Modifier,
) {
    val colors = LocalVitalisColors.current
    if (pageCount <= 0) {
        Box(
            modifier = modifier
                .fillMaxSize()
                .background(colors.bgApp),
            contentAlignment = Alignment.Center,
        ) {
            Text(
                text = "No PDF pages to display",
                color = colors.textMuted,
                style = MaterialTheme.typography.bodyMedium,
            )
        }
        return
    }

    LazyColumn(
        modifier = modifier
            .fillMaxSize()
            .background(colors.bgApp),
        contentPadding = PaddingValues(12.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        items((0 until pageCount).toList(), key = { it }) { pageIndex ->
            PdfPageItem(pdfFile = pdfFile, pageIndex = pageIndex)
        }
    }
}

@Composable
private fun PdfPageItem(
    pdfFile: File,
    pageIndex: Int,
) {
    val colors = LocalVitalisColors.current
    val bitmap by produceState<Bitmap?>(
        initialValue = null,
        key1 = pdfFile.absolutePath,
        key2 = pageIndex,
    ) {
        value = withContext(Dispatchers.IO) {
            renderPdfPage(pdfFile, pageIndex)
        }
    }

    if (bitmap == null) {
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .background(colors.bgInput)
                .padding(vertical = 28.dp),
            contentAlignment = Alignment.Center,
        ) {
            CircularProgressIndicator(modifier = Modifier.size(26.dp))
        }
        return
    }

    val renderedBitmap = bitmap!!

    Image(
        bitmap = renderedBitmap.asImageBitmap(),
        contentDescription = "Report page ${pageIndex + 1}",
        modifier = Modifier.fillMaxWidth(),
        contentScale = ContentScale.FillWidth,
    )

    Text(
        text = "Page ${pageIndex + 1}",
        style = MaterialTheme.typography.labelSmall,
        color = colors.textMuted,
        modifier = Modifier.padding(top = 2.dp),
    )
}

private fun renderPdfPage(pdfFile: File, pageIndex: Int): Bitmap? {
    var descriptor: ParcelFileDescriptor? = null
    var renderer: PdfRenderer? = null
    var page: PdfRenderer.Page? = null

    return try {
        descriptor = ParcelFileDescriptor.open(pdfFile, ParcelFileDescriptor.MODE_READ_ONLY)
        renderer = PdfRenderer(descriptor)
        if (pageIndex !in 0 until renderer.pageCount) {
            return null
        }

        page = renderer.openPage(pageIndex)
        val scale = 2
        val width = (page.width * scale).coerceAtLeast(1)
        val height = (page.height * scale).coerceAtLeast(1)

        val bitmap = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888)
        bitmap.eraseColor(AndroidColor.WHITE)
        page.render(bitmap, null, null, PdfRenderer.Page.RENDER_MODE_FOR_DISPLAY)
        bitmap
    } catch (_: Exception) {
        null
    } finally {
        page?.close()
        renderer?.close()
        descriptor?.close()
    }
}
