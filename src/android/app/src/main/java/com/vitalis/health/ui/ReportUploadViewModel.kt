package com.vitalis.health.ui

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.vitalis.health.data.model.ProcessReportResponse
import com.vitalis.health.data.network.ApiResult
import com.vitalis.health.data.repository.HealthRepository
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

/**
 * ViewModel for the Report Upload screen.
 *
 * Manages the async upload + background processing pipeline via [HealthRepository.ingestReport].
 */
class ReportUploadViewModel(
    private val repository: HealthRepository
) : ViewModel() {

    /** Possible states of the upload + processing pipeline. */
    sealed class UiState {
        data object Idle : UiState()
        data object Uploading : UiState()
        data class Processing(val status: String, val reportId: String) : UiState()
        data class Success(val result: ProcessReportResponse) : UiState()
        data class Error(val message: String) : UiState()
    }

    private val _uiState = MutableLiveData<UiState>(UiState.Idle)
    val uiState: LiveData<UiState> = _uiState

    /** Whether to use Gemini AI extraction (true) or standard regex (false). */
    private val _useGemini = MutableLiveData(false)
    val useGemini: LiveData<Boolean> = _useGemini

    fun setUseGemini(enabled: Boolean) {
        _useGemini.value = enabled
    }

    /**
     * Run the async pipeline: upload file, poll status until complete.
     *
     * Calls [HealthRepository.ingestReport] which maps to `POST /reports/ingest` (async).
     * Then polls [HealthRepository.getReportStatus] until status is "done" or "failed".
     */
    fun uploadAndProcess(userId: String, fileName: String, fileBytes: ByteArray) {
        _uiState.value = UiState.Uploading

        viewModelScope.launch {
            // Step 1: Upload and queue background processing
            val ingestResult = repository.ingestReport(
                userId = userId,
                userName = null, // Could be retrieved from user profile if needed
                fileName = fileName,
                fileBytes = fileBytes
            )

            when (ingestResult) {
                is ApiResult.Error -> {
                    _uiState.postValue(UiState.Error(ingestResult.message))
                    return@launch
                }
                is ApiResult.Success -> {
                    val reportId = ingestResult.data.reportId
                    val storagePath = ingestResult.data.storagePath
                    val publicUrl = ingestResult.data.publicUrl

                    // Step 2: Poll status until done or failed
                    pollReportStatus(reportId, storagePath, publicUrl)
                }
            }
        }
    }

    /**
     * Poll GET /reports/status/{reportId} until processing completes.
     * Updates UI state with progress, then builds final result when done.
     */
    private suspend fun pollReportStatus(reportId: String, storagePath: String, publicUrl: String) {
        var currentStatus = "pending"
        val maxAttempts = 60 // Poll for up to 2 minutes (60 * 2s = 120s)
        var attempts = 0

        while (currentStatus !in listOf("done", "failed") && attempts < maxAttempts) {
            delay(2000) // Poll every 2 seconds
            attempts++

            when (val statusResult = repository.getReportStatus(reportId)) {
                is ApiResult.Error -> {
                    _uiState.postValue(UiState.Error("Status check failed: ${statusResult.message}"))
                    return
                }
                is ApiResult.Success -> {
                    val status = statusResult.data
                    currentStatus = status.processingStatus

                    // Update UI with current progress
                    _uiState.postValue(UiState.Processing(currentStatus, reportId))

                    when (currentStatus) {
                        "done" -> {
                            // Build success response
                            val result = ProcessReportResponse(
                                reportId = reportId,
                                storagePath = storagePath,
                                publicUrl = publicUrl,
                                ocrConfidence = status.ocrConfidence ?: 0.0,
                                ocrTextPreview = "Processing complete. ${status.labResultsCount ?: 0} lab results extracted.",
                            )
                            _uiState.postValue(UiState.Success(result))
                            return
                        }
                        "failed" -> {
                            val error = status.processingError ?: "Processing failed"
                            _uiState.postValue(UiState.Error(error))
                            return
                        }
                    }
                }
            }
        }

        // Timeout
        if (attempts >= maxAttempts) {
            _uiState.postValue(
                UiState.Error("Processing timeout. Check report status later (ID: ${reportId.take(8)})")
            )
        }
    }

    /** Reset to idle so the user can upload another report. */
    fun reset() {
        _uiState.value = UiState.Idle
    }
}
