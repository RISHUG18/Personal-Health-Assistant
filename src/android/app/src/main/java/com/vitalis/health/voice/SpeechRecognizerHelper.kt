package com.vitalis.health.voice

import android.content.Context
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.os.SystemClock
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import android.content.Intent
import android.util.Log

class SpeechRecognizerHelper(private val context: Context) {

    private var speechRecognizer: SpeechRecognizer? = null
    private val mainHandler = Handler(Looper.getMainLooper())
    private var isInitializing = false
    private var hasBoundRecognizer = false
    private var isListeningInternal = false
    private var isStartPending = false
    private var pendingStartAfterInit = false
    private var lastStartRequestElapsedMs = 0L
    private var manualStopRequested = false
    private var hasRecognitionSinceListenStart = false
    private var lastSuccessfulRecognitionElapsedMs = 0L

    private val startDebounceMs = 700L
    private val reinitializeDelayMs = 250L
    private val benignClientErrorWindowMs = 1500L

    var onResult: ((String) -> Unit)? = null
    var onPartialResult: ((String) -> Unit)? = null
    var onError: ((String) -> Unit)? = null
    var onReady: (() -> Unit)? = null
    var onListeningStateChanged: ((Boolean) -> Unit)? = null

    fun initialize() {
        mainHandler.post {
            if (!SpeechRecognizer.isRecognitionAvailable(context)) {
                Log.e("VoiceAndroid", "[VOICE-ANDROID] Speech recognition not available")
                onError?.invoke("Speech recognition not available")
                return@post
            }

            if (speechRecognizer != null || isInitializing) {
                return@post
            }

            isInitializing = true

            try {
                speechRecognizer = SpeechRecognizer.createSpeechRecognizer(context)
                speechRecognizer?.setRecognitionListener(object : RecognitionListener {
                    override fun onReadyForSpeech(params: Bundle?) {
                        Log.d("VoiceAndroid", "[VOICE-ANDROID] Listening started")
                        manualStopRequested = false
                        hasRecognitionSinceListenStart = false
                        isStartPending = false
                        isListeningInternal = true
                        onListeningStateChanged?.invoke(true)
                        onReady?.invoke()
                    }

                    override fun onBeginningOfSpeech() {}
                    override fun onRmsChanged(rmsdB: Float) {}
                    override fun onBufferReceived(buffer: ByteArray?) {}

                    override fun onEndOfSpeech() {
                        Log.d("VoiceAndroid", "[VOICE-ANDROID] Listening stopped")
                        isStartPending = false
                        isListeningInternal = false
                        onListeningStateChanged?.invoke(false)
                    }

                    override fun onError(error: Int) {
                        val now = SystemClock.elapsedRealtime()
                        val hasRecentRecognition =
                            now - lastSuccessfulRecognitionElapsedMs <= benignClientErrorWindowMs
                        val suppressClientError = error == SpeechRecognizer.ERROR_CLIENT && (
                            manualStopRequested ||
                                hasRecognitionSinceListenStart ||
                                hasRecentRecognition
                            )

                        if (suppressClientError) {
                            Log.d(
                                "VoiceAndroid",
                                "[VOICE-ANDROID] Suppressed benign ERROR_CLIENT after stop/result"
                            )
                            manualStopRequested = false
                            isStartPending = false
                            isListeningInternal = false
                            onListeningStateChanged?.invoke(false)
                            return
                        }

                        val errorMessage = when (error) {
                            SpeechRecognizer.ERROR_AUDIO -> "Audio recording error"
                            SpeechRecognizer.ERROR_CLIENT -> "Client side error"
                            SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS -> "Insufficient permissions"
                            SpeechRecognizer.ERROR_NETWORK -> "Network error"
                            SpeechRecognizer.ERROR_NETWORK_TIMEOUT -> "Network timeout"
                            SpeechRecognizer.ERROR_NO_MATCH -> "No match"
                            SpeechRecognizer.ERROR_SPEECH_TIMEOUT -> "No speech input"
                            else -> "Unknown error"
                        }
                        Log.e("VoiceAndroid", "[VOICE-ANDROID] Error: $errorMessage")

                        manualStopRequested = false
                        isStartPending = false
                        isListeningInternal = false
                        onListeningStateChanged?.invoke(false)
                        onError?.invoke(errorMessage)

                        if (error == SpeechRecognizer.ERROR_CLIENT) {
                            recoverFromClientError()
                        }
                    }

                    override fun onResults(results: Bundle?) {
                        manualStopRequested = false
                        isStartPending = false
                        isListeningInternal = false
                        onListeningStateChanged?.invoke(false)

                        val matches = results?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                        if (!matches.isNullOrEmpty()) {
                            val text = matches[0]
                            Log.d("VoiceAndroid", "[VOICE-ANDROID] Recognized: $text")
                            hasRecognitionSinceListenStart = true
                            lastSuccessfulRecognitionElapsedMs = SystemClock.elapsedRealtime()
                            onPartialResult?.invoke(text)
                            onResult?.invoke(text)
                        }
                    }

                    override fun onPartialResults(partialResults: Bundle?) {
                        val partialMatches = partialResults
                            ?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                        val partialText = partialMatches?.firstOrNull()?.trim().orEmpty()
                        if (partialText.isNotEmpty()) {
                            hasRecognitionSinceListenStart = true
                            lastSuccessfulRecognitionElapsedMs = SystemClock.elapsedRealtime()
                            onPartialResult?.invoke(partialText)
                        }
                    }

                    override fun onEvent(eventType: Int, params: Bundle?) {}
                })
                hasBoundRecognizer = true
            } catch (exc: Exception) {
                Log.e("VoiceAndroid", "[VOICE-ANDROID] Failed to initialize recognizer", exc)
                hasBoundRecognizer = false
                speechRecognizer = null
                onError?.invoke("Client side error")
            } finally {
                isInitializing = false
                if (pendingStartAfterInit) {
                    pendingStartAfterInit = false
                    startListening()
                }
            }
        }
    }

    fun startListening() {
        mainHandler.post {
            if (isInitializing) {
                pendingStartAfterInit = true
                return@post
            }

            if (isListeningInternal || isStartPending) {
                return@post
            }

            if (speechRecognizer == null || !hasBoundRecognizer) {
                pendingStartAfterInit = true
                initialize()
                return@post
            }

            val now = SystemClock.elapsedRealtime()
            if (now - lastStartRequestElapsedMs < startDebounceMs) {
                return@post
            }
            lastStartRequestElapsedMs = now

            val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
                putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 1)
                putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)
                putExtra(RecognizerIntent.EXTRA_SPEECH_INPUT_COMPLETE_SILENCE_LENGTH_MILLIS, 1200L)
                putExtra(RecognizerIntent.EXTRA_SPEECH_INPUT_POSSIBLY_COMPLETE_SILENCE_LENGTH_MILLIS, 1200L)
            }

            manualStopRequested = false
            isStartPending = true
            try {
                speechRecognizer?.startListening(intent)
            } catch (exc: Exception) {
                Log.e("VoiceAndroid", "[VOICE-ANDROID] Failed to start listening", exc)
                isStartPending = false
                isListeningInternal = false
                onListeningStateChanged?.invoke(false)
                onError?.invoke("Client side error")
                recoverFromClientError()
            }
        }
    }

    fun stopListening() {
        mainHandler.post {
            manualStopRequested = true
            pendingStartAfterInit = false
            isStartPending = false
            isListeningInternal = false
            speechRecognizer?.stopListening()
            onListeningStateChanged?.invoke(false)
        }
    }

    fun destroy() {
        mainHandler.post {
            pendingStartAfterInit = false
            destroyRecognizer(notifyState = true)
        }
    }

    private fun recoverFromClientError() {
        destroyRecognizer(notifyState = false)
        mainHandler.postDelayed(
            { initialize() },
            reinitializeDelayMs,
        )
    }

    private fun destroyRecognizer(notifyState: Boolean) {
        isInitializing = false
        isStartPending = false
        isListeningInternal = false
        manualStopRequested = false
        hasRecognitionSinceListenStart = false
        hasBoundRecognizer = false
        if (notifyState) {
            onListeningStateChanged?.invoke(false)
        }
        speechRecognizer?.destroy()
        speechRecognizer = null
    }
}
