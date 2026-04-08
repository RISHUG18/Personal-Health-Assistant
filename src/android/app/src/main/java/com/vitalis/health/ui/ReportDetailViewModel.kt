package com.vitalis.health.ui

import android.graphics.pdf.PdfRenderer
import android.os.ParcelFileDescriptor
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.vitalis.health.data.network.ApiResult
import com.vitalis.health.data.repository.HealthRepository
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.File
import java.io.FileOutputStream
import java.net.HttpURLConnection
import java.net.URL

class ReportDetailViewModel(
    private val repository: HealthRepository
) : ViewModel() {

    sealed class PdfState {
        data object Idle : PdfState()
        data object Loading : PdfState()
        data class Ready(val file: File, val pageCount: Int) : PdfState()
        data class Error(val message: String) : PdfState()
    }

    private val _pdfState = MutableStateFlow<PdfState>(PdfState.Idle)
    val pdfState: StateFlow<PdfState> = _pdfState.asStateFlow()

    private var currentReportId: String? = null

    fun loadReportPdf(
        reportId: String,
        cacheDir: File,
        forceRefresh: Boolean = false,
    ) {
        if (!forceRefresh && currentReportId == reportId && _pdfState.value is PdfState.Ready) {
            return
        }

        currentReportId = reportId
        _pdfState.value = PdfState.Loading

        viewModelScope.launch {
            when (val signedUrlResult = repository.getReportDownloadUrl(reportId)) {
                is ApiResult.Error -> {
                    _pdfState.value = PdfState.Error(
                        "Failed to fetch secure report URL: ${signedUrlResult.message}"
                    )
                }

                is ApiResult.Success -> {
                    val downloadResult = downloadPdfToCache(
                        signedUrl = signedUrlResult.data,
                        reportId = reportId,
                        cacheDir = cacheDir,
                        forceRefresh = forceRefresh,
                    )

                    if (downloadResult.isFailure) {
                        _pdfState.value = PdfState.Error(
                            downloadResult.exceptionOrNull()?.message
                                ?: "Failed to download report PDF"
                        )
                        return@launch
                    }

                    val pdfFile = downloadResult.getOrNull()
                    if (pdfFile == null) {
                        _pdfState.value = PdfState.Error("Downloaded report file is missing")
                        return@launch
                    }

                    val pageCount = getPdfPageCount(pdfFile)
                    if (pageCount <= 0) {
                        _pdfState.value = PdfState.Error("Downloaded PDF has no renderable pages")
                        return@launch
                    }

                    _pdfState.value = PdfState.Ready(pdfFile, pageCount)
                }
            }
        }
    }

    private suspend fun downloadPdfToCache(
        signedUrl: String,
        reportId: String,
        cacheDir: File,
        forceRefresh: Boolean,
    ): Result<File> = withContext(Dispatchers.IO) {
        runCatching {
            val safeName = reportId.replace(Regex("[^a-zA-Z0-9_-]"), "_")
            val destination = File(cacheDir, "report_$safeName.pdf")
            if (destination.exists() && destination.length() > 0L && !forceRefresh) {
                return@runCatching destination
            }

            val tempFile = File(cacheDir, "report_${safeName}_${System.currentTimeMillis()}.tmp")
            var connection: HttpURLConnection? = null
            try {
                connection = (URL(signedUrl).openConnection() as HttpURLConnection).apply {
                    requestMethod = "GET"
                    connectTimeout = 15_000
                    readTimeout = 30_000
                    instanceFollowRedirects = true
                    connect()
                }

                val code = connection.responseCode
                if (code !in 200..299) {
                    throw IllegalStateException("Report download failed with HTTP $code")
                }

                connection.inputStream.use { input ->
                    FileOutputStream(tempFile).use { output ->
                        input.copyTo(output)
                    }
                }

                if (tempFile.length() <= 0L) {
                    throw IllegalStateException("Downloaded report PDF is empty")
                }

                if (destination.exists()) {
                    destination.delete()
                }
                if (!tempFile.renameTo(destination)) {
                    tempFile.copyTo(destination, overwrite = true)
                    tempFile.delete()
                }

                destination
            } finally {
                connection?.disconnect()
                if (tempFile.exists()) {
                    tempFile.delete()
                }
            }
        }
    }

    private fun getPdfPageCount(pdfFile: File): Int {
        var descriptor: ParcelFileDescriptor? = null
        var renderer: PdfRenderer? = null
        return try {
            descriptor = ParcelFileDescriptor.open(pdfFile, ParcelFileDescriptor.MODE_READ_ONLY)
            renderer = PdfRenderer(descriptor)
            renderer.pageCount
        } catch (_: Exception) {
            0
        } finally {
            renderer?.close()
            descriptor?.close()
        }
    }

    fun resetState() {
        _pdfState.value = PdfState.Idle
        currentReportId = null
    }
}
