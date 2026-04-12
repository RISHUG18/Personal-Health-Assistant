package com.vitalis.health.ui.components

import android.content.Context
import android.content.Intent
import android.widget.Toast
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.ArrowBack
import androidx.compose.material.icons.outlined.Share
import androidx.compose.material.icons.outlined.Shield
import androidx.compose.material3.AssistChip
import androidx.compose.material3.AssistChipDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.core.content.FileProvider
import com.vitalis.health.ui.ReportDetailViewModel
import com.vitalis.health.ui.theme.LocalVitalisColors
import com.vitalis.health.ui.theme.VitalisPrimary
import java.io.File
import java.util.Locale

@OptIn(androidx.compose.material3.ExperimentalMaterial3Api::class)
@Composable
fun ReportDetailScreen(
    reportId: String,
    originalReportName: String? = null,
    viewModel: ReportDetailViewModel,
    onBack: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val colors = LocalVitalisColors.current
    val context = LocalContext.current
    val pdfState by viewModel.pdfState.collectAsState()

    LaunchedEffect(reportId) {
        viewModel.loadReportPdf(reportId = reportId, cacheDir = context.cacheDir)
    }

    val readyState = pdfState as? ReportDetailViewModel.PdfState.Ready

    Scaffold(
        modifier = modifier.fillMaxSize(),
        containerColor = colors.bgApp,
        topBar = {
            TopAppBar(
                title = {
                    Text(
                        text = "Report Viewer",
                        fontWeight = FontWeight.Bold,
                        color = colors.textPrimary,
                    )
                },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(
                            imageVector = Icons.AutoMirrored.Outlined.ArrowBack,
                            contentDescription = "Back",
                            tint = colors.textPrimary,
                        )
                    }
                },
                actions = {
                    if (readyState != null) {
                        IconButton(
                            onClick = {
                                sharePdf(
                                    context = context,
                                    pdfFile = readyState.file,
                                    originalFileName = originalReportName,
                                )
                            }
                        ) {
                            Icon(
                                imageVector = Icons.Outlined.Share,
                                contentDescription = "Share report",
                                tint = VitalisPrimary,
                            )
                        }
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.surface,
                ),
            )
        },
    ) { padding ->
        when (val state = pdfState) {
            is ReportDetailViewModel.PdfState.Idle,
            is ReportDetailViewModel.PdfState.Loading -> {
                VitalisLoadingScreen(label = "Preparing secure report preview...")
            }

            is ReportDetailViewModel.PdfState.Error -> {
                Column(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(padding)
                        .background(colors.bgApp),
                    verticalArrangement = Arrangement.Top,
                ) {
                    VitalisErrorScreen(
                        title = "Report unavailable",
                        message = state.message,
                        onRetry = {
                            viewModel.loadReportPdf(
                                reportId = reportId,
                                cacheDir = context.cacheDir,
                                forceRefresh = true,
                            )
                        },
                    )
                }
            }

            is ReportDetailViewModel.PdfState.Ready -> {
                Column(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(padding)
                        .background(colors.bgApp),
                ) {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(horizontal = 12.dp, vertical = 10.dp),
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        AssistChip(
                            onClick = {},
                            label = {
                                Text(
                                    text = "Report ${reportId.take(8)}...",
                                    style = MaterialTheme.typography.labelMedium,
                                )
                            },
                            leadingIcon = {
                                Icon(
                                    imageVector = Icons.Outlined.Shield,
                                    contentDescription = null,
                                    modifier = Modifier.size(16.dp),
                                )
                            },
                            colors = AssistChipDefaults.assistChipColors(
                                containerColor = colors.primaryLight,
                                labelColor = VitalisPrimary,
                                leadingIconContentColor = VitalisPrimary,
                            ),
                        )

                        AssistChip(
                            onClick = {},
                            label = {
                                Text(
                                    text = "${state.pageCount} pages",
                                    style = MaterialTheme.typography.labelMedium,
                                )
                            },
                            colors = AssistChipDefaults.assistChipColors(
                                containerColor = colors.bgInput,
                                labelColor = colors.textSecondary,
                            ),
                        )
                    }

                    PdfRendererViewer(
                        pdfFile = state.file,
                        pageCount = state.pageCount,
                        modifier = Modifier.fillMaxSize(),
                    )
                }
            }
        }
    }
}

private fun sharePdf(
    context: Context,
    pdfFile: File,
    originalFileName: String?,
) {
    try {
        val shareFileName = buildShareFileName(originalFileName, pdfFile.name)
        val shareFile = File(context.cacheDir, shareFileName)
        pdfFile.copyTo(shareFile, overwrite = true)

        val uri = FileProvider.getUriForFile(
            context,
            "${context.packageName}.fileprovider",
            shareFile,
        )

        val shareIntent = Intent(Intent.ACTION_SEND).apply {
            type = "application/pdf"
            putExtra(Intent.EXTRA_STREAM, uri)
            putExtra(Intent.EXTRA_TITLE, shareFileName)
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }

        context.startActivity(Intent.createChooser(shareIntent, "Share report"))
    } catch (exc: Exception) {
        Toast.makeText(
            context,
            "Unable to share report: ${exc.message}",
            Toast.LENGTH_LONG,
        ).show()
    }
}

private fun buildShareFileName(originalFileName: String?, fallbackName: String): String {
    val sourceName = originalFileName
        ?.substringBeforeLast('.')
        ?.trim()
        .takeUnless { it.isNullOrBlank() }
        ?: fallbackName.substringBeforeLast('.').trim()

    val cleanedBaseName = sourceName
        .replace(Regex("[^A-Za-z0-9 _-]"), "")
        .replace(Regex("\\s+"), "_")
        .trim('_')
        .ifBlank { "Vitalis_Report" }

    val withReadableSuffix = if (cleanedBaseName.endsWith("_Report", ignoreCase = true)) {
        cleanedBaseName
    } else {
        "${cleanedBaseName}_Report"
    }

    return if (withReadableSuffix.lowercase(Locale.US).endsWith(".pdf")) {
        withReadableSuffix
    } else {
        "$withReadableSuffix.pdf"
    }
}
