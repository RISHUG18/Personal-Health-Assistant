package com.vitalis.health.ui

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.vitalis.health.data.model.ProcessReportResponse
import com.vitalis.health.data.network.ApiResult
import com.vitalis.health.data.repository.HealthRepository
import kotlinx.coroutines.launch

/**
 * ViewModel for the Report Upload screen.
 *
 * Manages the full upload → OCR → extraction pipeline via [HealthRepository.processReport].
 */
class ReportUploadViewModel(
    private val repository: HealthRepository
) : ViewModel() {

    /** Possible states of the upload + processing pipeline. */
    sealed class UiState {
        data object Idle : UiState()
        data object Uploading : UiState()
        data object Processing : UiState()
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
     * Run the full pipeline: upload the file, OCR it, extract lab results.
     *
     * Calls [HealthRepository.processReport] which maps to `POST /reports/process`.
     */
    fun uploadAndProcess(userId: String, fileName: String, fileBytes: ByteArray) {
        _uiState.value = UiState.Uploading

        viewModelScope.launch {
            // Brief uploading state, then processing
            _uiState.postValue(UiState.Processing)

            when (val result = repository.processReport(
                userId = userId,
                fileName = fileName,
                fileBytes = fileBytes,
                useGemini = _useGemini.value ?: false
            )) {
                is ApiResult.Success -> _uiState.postValue(UiState.Success(result.data))
                is ApiResult.Error   -> _uiState.postValue(UiState.Error(result.message))
            }
        }
    }

    /** Reset to idle so the user can upload another report. */
    fun reset() {
        _uiState.value = UiState.Idle
    }
}
