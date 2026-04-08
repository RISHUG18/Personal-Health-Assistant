package com.vitalis.health.ui.components

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.Crossfade
import androidx.compose.animation.animateColor
import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.VolumeUp
import androidx.compose.material.icons.filled.Mic
import androidx.compose.material.icons.outlined.Close
import androidx.compose.material.icons.outlined.StopCircle
import androidx.compose.material3.AssistChip
import androidx.compose.material3.AssistChipDefaults
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.vitalis.health.ui.theme.LocalVitalisColors
import com.vitalis.health.ui.theme.VitalisDanger
import com.vitalis.health.ui.theme.VitalisPrimary
import com.vitalis.health.ui.theme.VitalisWarning

enum class VoiceAssistantVisualState {
    Idle,
    Listening,
    Countdown,
    Processing,
    Speaking,
}

@Composable
fun VoiceAssistantOverlay(
    visible: Boolean,
    visualState: VoiceAssistantVisualState,
    transcript: String,
    countdownSeconds: Int?,
    statusMessage: String?,
    suggestionChips: List<String>,
    onDismiss: () -> Unit,
    onStartListening: () -> Unit,
    onStopListening: () -> Unit,
    onSendNow: () -> Unit,
    onSuggestionSelected: (String) -> Unit,
    onStopSpeaking: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val colors = LocalVitalisColors.current
    val displayText = remember(transcript) {
        transcript.ifBlank { "Start speaking..." }
    }

    AnimatedVisibility(
        visible = visible,
        enter = fadeIn(animationSpec = tween(220)),
        exit = fadeOut(animationSpec = tween(180)),
        modifier = modifier.fillMaxSize(),
    ) {
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(
                    Brush.verticalGradient(
                        listOf(
                            Color.Black.copy(alpha = 0.78f),
                            Color.Black.copy(alpha = 0.88f),
                        )
                    )
                )
                .padding(horizontal = 20.dp, vertical = 24.dp),
        ) {
            Column(
                modifier = Modifier.fillMaxSize(),
                verticalArrangement = Arrangement.SpaceBetween,
            ) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.End,
                ) {
                    IconButton(onClick = onDismiss) {
                        Icon(
                            imageVector = Icons.Outlined.Close,
                            contentDescription = "Close voice coach",
                            tint = Color.White,
                        )
                    }
                }

                Column(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.Center,
                ) {
                    CoachStateOrb(
                        state = visualState,
                        modifier = Modifier.size(182.dp),
                    )

                    Spacer(modifier = Modifier.height(18.dp))

                    Text(
                        text = when (visualState) {
                            VoiceAssistantVisualState.Idle -> "Your health coach is ready"
                            VoiceAssistantVisualState.Listening -> "Listening..."
                            VoiceAssistantVisualState.Countdown -> "Voice captured. Sending soon"
                            VoiceAssistantVisualState.Processing -> "Thinking through your context"
                            VoiceAssistantVisualState.Speaking -> "Explaining your health insight"
                        },
                        style = MaterialTheme.typography.titleMedium,
                        color = colors.textSecondary,
                        textAlign = TextAlign.Center,
                    )

                    Spacer(modifier = Modifier.height(14.dp))

                    Surface(
                        shape = RoundedCornerShape(20.dp),
                        color = colors.bgInput.copy(alpha = 0.18f),
                        modifier = Modifier.fillMaxWidth(),
                    ) {
                        Column(modifier = Modifier.padding(14.dp)) {
                            Crossfade(
                                targetState = displayText,
                                animationSpec = tween(durationMillis = 220),
                                label = "transcript_fade",
                            ) { liveText ->
                                Text(
                                    text = liveText,
                                    style = MaterialTheme.typography.headlineMedium,
                                    color = if (liveText == "Start speaking...") colors.textMuted else Color.White,
                                    textAlign = TextAlign.Center,
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .padding(vertical = 8.dp),
                                )
                            }

                            if (visualState == VoiceAssistantVisualState.Countdown && countdownSeconds != null) {
                                Spacer(modifier = Modifier.height(10.dp))
                                Text(
                                    text = "Sending in $countdownSeconds...",
                                    style = MaterialTheme.typography.labelLarge,
                                    color = VitalisWarning,
                                )
                            }

                            if (!statusMessage.isNullOrBlank()) {
                                Spacer(modifier = Modifier.height(10.dp))
                                Text(
                                    text = statusMessage,
                                    style = MaterialTheme.typography.bodyMedium,
                                    color = VitalisWarning,
                                )
                            }
                        }
                    }

                    Spacer(modifier = Modifier.height(16.dp))

                    when (visualState) {
                        VoiceAssistantVisualState.Idle -> {
                            Button(
                                onClick = onStartListening,
                                colors = ButtonDefaults.buttonColors(
                                    containerColor = VitalisPrimary,
                                    contentColor = Color.White,
                                ),
                            ) {
                                Icon(
                                    imageVector = Icons.Filled.Mic,
                                    contentDescription = null,
                                )
                                Spacer(modifier = Modifier.width(8.dp))
                                Text("Start listening", fontWeight = FontWeight.SemiBold)
                            }
                        }

                        VoiceAssistantVisualState.Listening -> {
                            Button(
                                onClick = onStopListening,
                                colors = ButtonDefaults.buttonColors(
                                    containerColor = VitalisWarning,
                                    contentColor = Color.White,
                                ),
                            ) {
                                Text("Finish speaking", fontWeight = FontWeight.SemiBold)
                            }
                        }

                        VoiceAssistantVisualState.Countdown -> {
                            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                                Button(
                                    onClick = onSendNow,
                                    enabled = transcript.isNotBlank(),
                                    colors = ButtonDefaults.buttonColors(
                                        containerColor = VitalisPrimary,
                                        contentColor = Color.White,
                                    ),
                                ) {
                                    Text("Send now", fontWeight = FontWeight.SemiBold)
                                }
                                Button(
                                    onClick = onStartListening,
                                    colors = ButtonDefaults.buttonColors(
                                        containerColor = colors.accent,
                                        contentColor = Color.White,
                                    ),
                                ) {
                                    Text("Listen again", fontWeight = FontWeight.SemiBold)
                                }
                            }
                        }

                        VoiceAssistantVisualState.Processing -> {
                            Text(
                                text = "Analyzing vitals, reports, and context...",
                                style = MaterialTheme.typography.bodyLarge,
                                color = colors.textMuted,
                            )
                        }

                        VoiceAssistantVisualState.Speaking -> {
                            Button(
                                onClick = onStopSpeaking,
                                colors = ButtonDefaults.buttonColors(
                                    containerColor = VitalisDanger,
                                    contentColor = Color.White,
                                ),
                            ) {
                                Icon(
                                    imageVector = Icons.Outlined.StopCircle,
                                    contentDescription = null,
                                )
                                Spacer(modifier = Modifier.width(8.dp))
                                Text("Stop coach audio", fontWeight = FontWeight.Bold)
                            }
                        }
                    }
                }

                if (suggestionChips.isNotEmpty()) {
                    Column {
                        Text(
                            text = "Try asking",
                            style = MaterialTheme.typography.labelLarge,
                            color = colors.textSecondary,
                            modifier = Modifier.padding(bottom = 10.dp),
                        )
                        LazyRow(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                            items(suggestionChips.take(3)) { chip ->
                                AssistChip(
                                    onClick = { onSuggestionSelected(chip) },
                                    label = {
                                        Text(
                                            text = chip,
                                            style = MaterialTheme.typography.labelMedium,
                                        )
                                    },
                                    colors = AssistChipDefaults.assistChipColors(
                                        containerColor = colors.bgInput.copy(alpha = 0.28f),
                                        labelColor = Color.White,
                                    ),
                                )
                            }
                        }
                    }
                } else {
                    Spacer(modifier = Modifier.height(12.dp))
                }
            }
        }
    }
}

@Composable
private fun CoachStateOrb(
    state: VoiceAssistantVisualState,
    modifier: Modifier = Modifier,
) {
    when (state) {
        VoiceAssistantVisualState.Idle -> IdleCoachOrb(modifier)
        VoiceAssistantVisualState.Listening -> ListeningCoachOrb(modifier)
        VoiceAssistantVisualState.Countdown -> ProcessingCoachOrb(modifier, countdownMode = true)
        VoiceAssistantVisualState.Processing -> ProcessingCoachOrb(modifier, countdownMode = false)
        VoiceAssistantVisualState.Speaking -> SpeakingCoachOrb(modifier)
    }
}

@Composable
private fun IdleCoachOrb(modifier: Modifier = Modifier) {
    val transition = rememberInfiniteTransition(label = "idle_orb")
    val pulseScale by transition.animateFloat(
        initialValue = 0.92f,
        targetValue = 1.08f,
        animationSpec = infiniteRepeatable(
            animation = tween(durationMillis = 950, easing = LinearEasing),
            repeatMode = RepeatMode.Reverse,
        ),
        label = "idle_scale",
    )
    val pulseAlpha by transition.animateFloat(
        initialValue = 0.2f,
        targetValue = 0.42f,
        animationSpec = infiniteRepeatable(
            animation = tween(durationMillis = 950, easing = LinearEasing),
            repeatMode = RepeatMode.Reverse,
        ),
        label = "idle_alpha",
    )

    Box(modifier = modifier, contentAlignment = Alignment.Center) {
        Box(
            modifier = Modifier
                .fillMaxSize()
                .graphicsLayer(
                    scaleX = pulseScale,
                    scaleY = pulseScale,
                    alpha = pulseAlpha,
                )
                .clip(CircleShape)
                .background(VitalisPrimary.copy(alpha = 0.28f)),
        )
        Box(
            modifier = Modifier
                .size(126.dp)
                .clip(CircleShape)
                .background(VitalisPrimary),
            contentAlignment = Alignment.Center,
        ) {
            Icon(
                imageVector = Icons.Filled.Mic,
                contentDescription = null,
                tint = Color.White,
                modifier = Modifier.size(48.dp),
            )
        }
    }
}

@Composable
private fun ListeningCoachOrb(modifier: Modifier = Modifier) {
    val colors = LocalVitalisColors.current
    val transition = rememberInfiniteTransition(label = "listening_orb")

    val ringScaleA by transition.animateFloat(
        initialValue = 0.68f,
        targetValue = 1.35f,
        animationSpec = infiniteRepeatable(
            animation = tween(durationMillis = 900, easing = LinearEasing),
            repeatMode = RepeatMode.Restart,
        ),
        label = "ring_a_scale",
    )
    val ringScaleB by transition.animateFloat(
        initialValue = 0.82f,
        targetValue = 1.5f,
        animationSpec = infiniteRepeatable(
            animation = tween(durationMillis = 1150, easing = LinearEasing),
            repeatMode = RepeatMode.Restart,
        ),
        label = "ring_b_scale",
    )
    val listeningColor by transition.animateColor(
        initialValue = colors.accent,
        targetValue = VitalisWarning,
        animationSpec = infiniteRepeatable(
            animation = tween(durationMillis = 1250, easing = LinearEasing),
            repeatMode = RepeatMode.Reverse,
        ),
        label = "listening_color",
    )

    Box(modifier = modifier, contentAlignment = Alignment.Center) {
        Box(
            modifier = Modifier
                .fillMaxSize()
                .graphicsLayer(
                    scaleX = ringScaleB,
                    scaleY = ringScaleB,
                    alpha = 0.16f,
                )
                .clip(CircleShape)
                .background(listeningColor),
        )
        Box(
            modifier = Modifier
                .fillMaxSize()
                .graphicsLayer(
                    scaleX = ringScaleA,
                    scaleY = ringScaleA,
                    alpha = 0.24f,
                )
                .clip(CircleShape)
                .background(listeningColor),
        )
        Box(
            modifier = Modifier
                .size(122.dp)
                .clip(CircleShape)
                .background(listeningColor),
            contentAlignment = Alignment.Center,
        ) {
            Icon(
                imageVector = Icons.Filled.Mic,
                contentDescription = null,
                tint = Color.White,
                modifier = Modifier.size(46.dp),
            )
        }
    }
}

@Composable
private fun ProcessingCoachOrb(
    modifier: Modifier = Modifier,
    countdownMode: Boolean,
) {
    val colors = LocalVitalisColors.current
    val transition = rememberInfiniteTransition(label = "processing_orb")
    val rotation by transition.animateFloat(
        initialValue = 0f,
        targetValue = 360f,
        animationSpec = infiniteRepeatable(
            animation = tween(durationMillis = if (countdownMode) 2200 else 1450, easing = LinearEasing),
            repeatMode = RepeatMode.Restart,
        ),
        label = "processing_rotation",
    )

    val centerScale by animateFloatAsState(
        targetValue = if (countdownMode) 0.84f else 1f,
        animationSpec = tween(220),
        label = "center_scale",
    )

    Box(modifier = modifier, contentAlignment = Alignment.Center) {
        Box(
            modifier = Modifier
                .fillMaxSize()
                .graphicsLayer { rotationZ = rotation }
                .clip(CircleShape)
                .background(
                    Brush.sweepGradient(
                        listOf(
                            colors.accent,
                            VitalisPrimary,
                            VitalisWarning,
                            colors.accent,
                        )
                    )
                ),
        )

        Box(
            modifier = Modifier
                .size(132.dp)
                .graphicsLayer {
                    scaleX = centerScale
                    scaleY = centerScale
                }
                .clip(CircleShape)
                .background(Color.Black.copy(alpha = 0.58f)),
            contentAlignment = Alignment.Center,
        ) {
            Text(
                text = if (countdownMode) "Queued" else "Thinking",
                style = MaterialTheme.typography.titleMedium,
                color = Color.White,
            )
        }
    }
}

@Composable
private fun SpeakingCoachOrb(modifier: Modifier = Modifier) {
    val transition = rememberInfiniteTransition(label = "speaking_orb")

    val bars = listOf(320, 420, 510, 460, 350)
    val barLevels = bars.mapIndexed { index, duration ->
        transition.animateFloat(
            initialValue = 0.25f,
            targetValue = 1f,
            animationSpec = infiniteRepeatable(
                animation = tween(durationMillis = duration + (index * 40), easing = LinearEasing),
                repeatMode = RepeatMode.Reverse,
            ),
            label = "speaking_bar_$index",
        )
    }

    Box(
        modifier = modifier
            .clip(CircleShape)
            .background(VitalisPrimary.copy(alpha = 0.2f)),
        contentAlignment = Alignment.Center,
    ) {
        Row(
            horizontalArrangement = Arrangement.spacedBy(6.dp),
            verticalAlignment = Alignment.Bottom,
        ) {
            barLevels.forEach { bar ->
                Box(
                    modifier = Modifier
                        .width(10.dp)
                        .height((20 + (54 * bar.value)).dp)
                        .clip(RoundedCornerShape(999.dp))
                        .background(Color.White),
                )
            }
        }

        Icon(
            imageVector = Icons.AutoMirrored.Outlined.VolumeUp,
            contentDescription = null,
            tint = Color.White.copy(alpha = 0.86f),
            modifier = Modifier
                .align(Alignment.TopCenter)
                .padding(top = 20.dp)
                .size(22.dp),
        )
    }
}
