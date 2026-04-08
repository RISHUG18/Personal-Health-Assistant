package com.vitalis.health.ui.components

import androidx.compose.animation.Crossfade
import androidx.compose.animation.core.tween
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.Send
import androidx.compose.material.icons.automirrored.outlined.VolumeUp
import androidx.compose.material.icons.filled.Mic
import androidx.compose.material.icons.outlined.StopCircle
import androidx.compose.material3.AssistChip
import androidx.compose.material3.AssistChipDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.runtime.livedata.observeAsState
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.focus.onFocusChanged
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.dp
import com.vitalis.health.ui.AssistantViewModel
import com.vitalis.health.ui.theme.LocalVitalisColors
import com.vitalis.health.ui.theme.VitalisDanger
import com.vitalis.health.ui.theme.VitalisPrimary

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ChatScreen(
    vm: AssistantViewModel,
    userId: String,
    isListening: Boolean,
    isSpeaking: Boolean,
    voiceOverlayVisible: Boolean,
    voiceOverlayState: VoiceAssistantVisualState,
    voiceTranscript: String,
    voiceCountdownSeconds: Int?,
    voiceStatusMessage: String?,
    voiceSuggestionChips: List<String>,
    onVoiceInput: () -> Unit,
    onSpeakMessage: (String) -> Unit,
    onStopSpeaking: () -> Unit,
    onTextModeActivated: () -> Unit,
    onOverlayDismiss: () -> Unit,
    onOverlayStartListening: () -> Unit,
    onOverlayStopListening: () -> Unit,
    onOverlaySendNow: () -> Unit,
    onOverlaySuggestionSelected: (String) -> Unit,
    modifier: Modifier = Modifier,
) {
    val colors = LocalVitalisColors.current
    val chatHistory by vm.chatHistory.observeAsState(emptyList())
    val uiState by vm.uiState.observeAsState(AssistantViewModel.UiState.Idle)

    var queryText by remember { mutableStateOf("") }
    val hasTypedText = queryText.trim().isNotEmpty()
    val isLoading = uiState is AssistantViewModel.UiState.Loading

    val listState = rememberLazyListState()
    val latestAssistantIndex = remember(chatHistory) { chatHistory.indexOfLast { !it.isUser } }
    val transientRows = if (uiState is AssistantViewModel.UiState.Loading || uiState is AssistantViewModel.UiState.Error) {
        1
    } else {
        0
    }

    LaunchedEffect(chatHistory.size, transientRows) {
        val targetIndex = chatHistory.size + transientRows - 1
        if (targetIndex >= 0) {
            listState.animateScrollToItem(targetIndex)
        }
    }

    val sendTextMessage: () -> Unit = {
        val cleaned = queryText.trim()
        if (cleaned.isNotEmpty()) {
            onTextModeActivated()
            vm.sendQuery(userId, cleaned)
            queryText = ""
        }
    }

    Box(
        modifier = modifier
            .fillMaxSize()
            .background(colors.bgApp),
    ) {
        androidx.compose.foundation.layout.Column(
            modifier = Modifier.fillMaxSize(),
        ) {
            LazyColumn(
                state = listState,
                modifier = Modifier
                    .weight(1f)
                    .fillMaxWidth(),
                contentPadding = PaddingValues(16.dp),
                verticalArrangement = Arrangement.spacedBy(10.dp),
            ) {
                if (chatHistory.isEmpty() && uiState !is AssistantViewModel.UiState.Loading) {
                    item {
                        Box(
                            modifier = Modifier
                                .fillParentMaxSize()
                                .padding(horizontal = 4.dp),
                            contentAlignment = Alignment.Center,
                        ) {
                            androidx.compose.foundation.layout.Column(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalAlignment = Alignment.Start,
                                verticalArrangement = Arrangement.spacedBy(10.dp),
                            ) {
                                Text(
                                    text = "Try asking",
                                    style = MaterialTheme.typography.labelLarge,
                                    color = colors.textSecondary,
                                )

                                LazyRow(
                                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                                ) {
                                    items(voiceSuggestionChips) { suggestion ->
                                        AssistChip(
                                            onClick = {
                                                queryText = suggestion
                                                sendTextMessage()
                                            },
                                            label = {
                                                Text(
                                                    text = suggestion,
                                                    style = MaterialTheme.typography.bodySmall,
                                                )
                                            },
                                            colors = AssistChipDefaults.assistChipColors(
                                                containerColor = colors.bgInput.copy(alpha = 0.28f),
                                                labelColor = colors.textPrimary,
                                            ),
                                            border = BorderStroke(1.dp, colors.borderLight),
                                        )
                                    }
                                }
                            }
                        }
                    }
                }

                itemsIndexed(chatHistory) { index, msg ->
                    val isActiveAssistantMessage = !msg.isUser && index == latestAssistantIndex
                    val bubbleColor = if (msg.isUser) colors.primaryLight else MaterialTheme.colorScheme.surface
                    val bubbleBorder = if (msg.isUser) {
                        VitalisPrimary.copy(alpha = 0.28f)
                    } else {
                        colors.borderLight
                    }
                    val bubbleShape = if (msg.isUser) {
                        RoundedCornerShape(topStart = 16.dp, topEnd = 16.dp, bottomStart = 16.dp, bottomEnd = 6.dp)
                    } else {
                        RoundedCornerShape(topStart = 16.dp, topEnd = 16.dp, bottomStart = 6.dp, bottomEnd = 16.dp)
                    }

                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = if (msg.isUser) Arrangement.End else Arrangement.Start,
                    ) {
                        Surface(
                            modifier = Modifier.fillMaxWidth(0.9f),
                            color = bubbleColor,
                            shape = bubbleShape,
                            border = BorderStroke(1.dp, bubbleBorder),
                            tonalElevation = 0.dp,
                        ) {
                            androidx.compose.foundation.layout.Column(
                                modifier = Modifier.padding(12.dp),
                            ) {
                                Text(
                                    text = if (msg.isUser) "You" else "Coach",
                                    style = MaterialTheme.typography.labelSmall,
                                    color = colors.textMuted,
                                )
                                Spacer(modifier = Modifier.height(4.dp))
                                Text(
                                    text = parseMarkdownBold(msg.text),
                                    style = MaterialTheme.typography.bodyMedium,
                                    color = colors.textPrimary,
                                )

                                if (msg.citations.isNotEmpty()) {
                                    Spacer(modifier = Modifier.height(6.dp))
                                    msg.citations.forEach { citation ->
                                        Text(
                                            text = "[${citation.sourceFile} p.${citation.page}] ${citation.snippet}",
                                            style = MaterialTheme.typography.bodySmall,
                                            color = colors.textMuted,
                                        )
                                    }
                                }

                                if (!msg.isUser) {
                                    Spacer(modifier = Modifier.height(6.dp))
                                    Row(
                                        modifier = Modifier.fillMaxWidth(),
                                        horizontalArrangement = Arrangement.End,
                                    ) {
                                        if (isSpeaking && isActiveAssistantMessage) {
                                            AssistChip(
                                                onClick = onStopSpeaking,
                                                label = {
                                                    Text(
                                                        text = "Stop Audio",
                                                        style = MaterialTheme.typography.labelMedium,
                                                        fontWeight = FontWeight.SemiBold,
                                                    )
                                                },
                                                leadingIcon = {
                                                    Icon(
                                                        imageVector = Icons.Outlined.StopCircle,
                                                        contentDescription = "Stop audio",
                                                        modifier = Modifier.size(16.dp),
                                                    )
                                                },
                                                colors = AssistChipDefaults.assistChipColors(
                                                    containerColor = colors.dangerBg,
                                                    labelColor = VitalisDanger,
                                                    leadingIconContentColor = VitalisDanger,
                                                ),
                                            )
                                        } else {
                                            IconButton(
                                                onClick = { onSpeakMessage(msg.text) },
                                                modifier = Modifier.size(30.dp),
                                            ) {
                                                Icon(
                                                    imageVector = Icons.AutoMirrored.Outlined.VolumeUp,
                                                    contentDescription = "Read response",
                                                    tint = colors.textMuted,
                                                    modifier = Modifier.size(18.dp),
                                                )
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }

                if (uiState is AssistantViewModel.UiState.Loading) {
                    item {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.Start,
                            verticalAlignment = Alignment.CenterVertically,
                        ) {
                            CircularProgressIndicator(
                                modifier = Modifier
                                    .padding(8.dp)
                                    .size(24.dp),
                                strokeWidth = 2.dp,
                                color = MaterialTheme.colorScheme.primary,
                            )
                            Text(
                                text = "Processing...",
                                style = MaterialTheme.typography.bodySmall,
                                color = colors.textMuted,
                            )
                        }
                    }
                }

                if (uiState is AssistantViewModel.UiState.Error) {
                    item {
                        val errorText = (uiState as AssistantViewModel.UiState.Error).message
                        Surface(
                            modifier = Modifier
                                .fillMaxWidth(0.85f)
                                .padding(vertical = 4.dp),
                            shape = MaterialTheme.shapes.medium,
                            color = MaterialTheme.colorScheme.errorContainer,
                        ) {
                            Text(
                                text = "Error: $errorText",
                                modifier = Modifier.padding(12.dp),
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onErrorContainer,
                            )
                        }
                    }
                }
            }

            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(MaterialTheme.colorScheme.surface)
                    .padding(12.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(10.dp),
            ) {
                OutlinedTextField(
                    value = queryText,
                    onValueChange = {
                        queryText = it
                        onTextModeActivated()
                    },
                    modifier = Modifier
                        .weight(1f)
                        .onFocusChanged { state ->
                            if (state.isFocused) {
                                onTextModeActivated()
                            }
                        },
                    placeholder = {
                        Text(
                            text = "Ask a health question...",
                            color = colors.textMuted,
                        )
                    },
                    textStyle = MaterialTheme.typography.bodyMedium.copy(color = colors.textPrimary),
                    singleLine = true,
                    shape = RoundedCornerShape(999.dp),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedBorderColor = VitalisPrimary,
                        unfocusedBorderColor = colors.borderLight,
                        focusedContainerColor = MaterialTheme.colorScheme.surface,
                        unfocusedContainerColor = MaterialTheme.colorScheme.surface,
                    ),
                )

                Surface(
                    shape = CircleShape,
                    color = if (hasTypedText) VitalisPrimary else colors.bgInput,
                    border = BorderStroke(1.dp, colors.borderLight),
                    tonalElevation = if (hasTypedText) 2.dp else 0.dp,
                    modifier = Modifier.size(44.dp),
                ) {
                    IconButton(
                        onClick = {
                            if (hasTypedText) {
                                sendTextMessage()
                            } else {
                                onVoiceInput()
                            }
                        },
                        enabled = !isLoading,
                    ) {
                        Crossfade(
                            targetState = hasTypedText,
                            animationSpec = tween(durationMillis = 180),
                            label = "chat_action_crossfade",
                        ) { showSend ->
                            Icon(
                                imageVector = if (showSend) Icons.AutoMirrored.Filled.Send else Icons.Filled.Mic,
                                contentDescription = if (showSend) "Send message" else "Start voice input",
                                tint = if (showSend) Color.White else if (isListening) VitalisPrimary else colors.textSecondary,
                            )
                        }
                    }
                }
            }
        }

        VoiceAssistantOverlay(
            visible = voiceOverlayVisible,
            visualState = voiceOverlayState,
            transcript = voiceTranscript,
            countdownSeconds = voiceCountdownSeconds,
            statusMessage = voiceStatusMessage,
            suggestionChips = voiceSuggestionChips,
            onDismiss = onOverlayDismiss,
            onStartListening = onOverlayStartListening,
            onStopListening = onOverlayStopListening,
            onSendNow = onOverlaySendNow,
            onSuggestionSelected = onOverlaySuggestionSelected,
            onStopSpeaking = onStopSpeaking,
        )
    }
}

private fun parseMarkdownBold(text: String): AnnotatedString {
    if (!text.contains("**")) return AnnotatedString(text)

    val boldRegex = Regex("\\*\\*(.+?)\\*\\*")
    return buildAnnotatedString {
        var cursor = 0
        boldRegex.findAll(text).forEach { match ->
            val start = match.range.first
            val endExclusive = match.range.last + 1

            if (start > cursor) {
                append(text.substring(cursor, start))
            }

            withStyle(SpanStyle(fontWeight = FontWeight.Bold)) {
                append(match.groupValues[1])
            }
            cursor = endExclusive
        }

        if (cursor < text.length) {
            append(text.substring(cursor))
        }
    }
}
