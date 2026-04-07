package com.vitalis.health.voice

import android.content.Context
import android.speech.tts.TextToSpeech
import android.speech.tts.UtteranceProgressListener
import android.util.Log
import java.util.Locale

class TTSHelper(private val context: Context) : TextToSpeech.OnInitListener {
    private var tts: TextToSpeech? = null
    var isInitialized = false
    var onSpeakingStateChanged: ((Boolean) -> Unit)? = null

    fun initialize() {
        tts = TextToSpeech(context, this)
    }

    override fun onInit(status: Int) {
        if (status == TextToSpeech.SUCCESS) {
            val result = tts?.setLanguage(Locale.US)
            if (result == TextToSpeech.LANG_MISSING_DATA || result == TextToSpeech.LANG_NOT_SUPPORTED) {
                Log.e("VoiceAndroid", "[VOICE-ANDROID] TTS Language not supported")
                isInitialized = false
            } else {
                Log.d("VoiceAndroid", "[VOICE-ANDROID] TTS Initialized successfully")
                tts?.setOnUtteranceProgressListener(object : UtteranceProgressListener() {
                    override fun onStart(utteranceId: String?) {
                        onSpeakingStateChanged?.invoke(true)
                    }

                    override fun onDone(utteranceId: String?) {
                        onSpeakingStateChanged?.invoke(false)
                    }

                    @Deprecated("Deprecated in Java")
                    override fun onError(utteranceId: String?) {
                        onSpeakingStateChanged?.invoke(false)
                    }
                })
                isInitialized = true
            }
        } else {
            Log.e("VoiceAndroid", "[VOICE-ANDROID] TTS Initialization failed")
            isInitialized = false
        }
    }

    fun speak(text: String) {
        if (isInitialized) {
            Log.d("VoiceAndroid", "[VOICE-ANDROID] Speaking response: $text")
            onSpeakingStateChanged?.invoke(true)
            val utteranceId = "voice_${System.currentTimeMillis()}"
            tts?.speak(text, TextToSpeech.QUEUE_FLUSH, null, utteranceId)
        } else {
            Log.e("VoiceAndroid", "[VOICE-ANDROID] TTS is not initialized")
        }
    }

    fun stop() {
        tts?.stop()
        onSpeakingStateChanged?.invoke(false)
    }

    fun destroy() {
        stop()
        tts?.shutdown()
        tts = null
    }
}
