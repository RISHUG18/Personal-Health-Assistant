package com.vitalis.health.voice

import android.content.Context
import android.os.Bundle
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import android.content.Intent
import android.util.Log

class SpeechRecognizerHelper(private val context: Context) {

    private var speechRecognizer: SpeechRecognizer? = null
    var onResult: ((String) -> Unit)? = null
    var onPartialResult: ((String) -> Unit)? = null
    var onError: ((String) -> Unit)? = null
    var onReady: (() -> Unit)? = null
    var onListeningStateChanged: ((Boolean) -> Unit)? = null

    fun initialize() {
        if (SpeechRecognizer.isRecognitionAvailable(context)) {
            speechRecognizer = SpeechRecognizer.createSpeechRecognizer(context)
            speechRecognizer?.setRecognitionListener(object : RecognitionListener {
                override fun onReadyForSpeech(params: Bundle?) {
                    Log.d("VoiceAndroid", "[VOICE-ANDROID] Listening started")
                    onListeningStateChanged?.invoke(true)
                    onReady?.invoke()
                }

                override fun onBeginningOfSpeech() {}
                override fun onRmsChanged(rmsdB: Float) {}
                override fun onBufferReceived(buffer: ByteArray?) {}
                override fun onEndOfSpeech() {
                    Log.d("VoiceAndroid", "[VOICE-ANDROID] Listening stopped")
                    onListeningStateChanged?.invoke(false)
                }

                override fun onError(error: Int) {
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
                    onListeningStateChanged?.invoke(false)
                    onError?.invoke(errorMessage)
                }

                override fun onResults(results: Bundle?) {
                    val matches = results?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                    if (!matches.isNullOrEmpty()) {
                        val text = matches[0]
                        Log.d("VoiceAndroid", "[VOICE-ANDROID] Recognized: $text")
                        onPartialResult?.invoke(text)
                        onListeningStateChanged?.invoke(false)
                        onResult?.invoke(text)
                    }
                }

                override fun onPartialResults(partialResults: Bundle?) {
                    val partialMatches = partialResults
                        ?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                    val partialText = partialMatches?.firstOrNull()?.trim().orEmpty()
                    if (partialText.isNotEmpty()) {
                        onPartialResult?.invoke(partialText)
                    }
                }
                override fun onEvent(eventType: Int, params: Bundle?) {}
            })
        } else {
            Log.e("VoiceAndroid", "[VOICE-ANDROID] Speech recognition not available")
            onError?.invoke("Speech recognition not available")
        }
    }

    fun startListening() {
        val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 1)
            putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)
            putExtra(RecognizerIntent.EXTRA_SPEECH_INPUT_COMPLETE_SILENCE_LENGTH_MILLIS, 1200L)
            putExtra(RecognizerIntent.EXTRA_SPEECH_INPUT_POSSIBLY_COMPLETE_SILENCE_LENGTH_MILLIS, 1200L)
        }
        onListeningStateChanged?.invoke(true)
        speechRecognizer?.startListening(intent)
    }

    fun stopListening() {
        speechRecognizer?.stopListening()
        onListeningStateChanged?.invoke(false)
    }

    fun destroy() {
        onListeningStateChanged?.invoke(false)
        speechRecognizer?.destroy()
        speechRecognizer = null
    }
}
