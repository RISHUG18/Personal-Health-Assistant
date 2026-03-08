package com.vitalis.health.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Shapes
import androidx.compose.material3.Typography
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.foundation.shape.RoundedCornerShape

// ─── Design tokens from sample.html ──────────────────────────────────────────

val VitalisPrimary       = Color(0xFF10785A)
val VitalisPrimaryDark   = Color(0xFF0B5E46)
val VitalisPrimaryLight  = Color(0xFFE8F5F0)
val VitalisPrimaryMuted  = Color(0xFFB4D7CC)

val VitalisBgApp         = Color(0xFFF5F7F6)
val VitalisBgCard        = Color(0xFFFFFFFF)
val VitalisBgInput       = Color(0xFFF0F2F1)

val VitalisTextPrimary   = Color(0xFF1A2B25)
val VitalisTextSecondary = Color(0xFF506B60)
val VitalisTextMuted     = Color(0xFF8FA69B)

val VitalisWarning       = Color(0xFFC27817)
val VitalisDanger        = Color(0xFFC0392B)
val VitalisSuccess       = Color(0xFF1E7D5A)
val VitalisBorder        = Color(0xFFDAE3DE)

// ─── Color schemes ───────────────────────────────────────────────────────────

private val LightColorScheme = lightColorScheme(
    primary              = VitalisPrimary,
    onPrimary            = Color.White,
    primaryContainer     = VitalisPrimaryLight,
    onPrimaryContainer   = VitalisPrimaryDark,
    secondary            = VitalisTextSecondary,
    onSecondary          = Color.White,
    secondaryContainer   = VitalisBgInput,
    onSecondaryContainer = VitalisTextPrimary,
    background           = VitalisBgApp,
    onBackground         = VitalisTextPrimary,
    surface              = VitalisBgCard,
    onSurface            = VitalisTextPrimary,
    surfaceVariant       = VitalisBgInput,
    onSurfaceVariant     = VitalisTextSecondary,
    error                = VitalisDanger,
    onError              = Color.White,
    errorContainer       = Color(0xFFFFF0EE),
    onErrorContainer     = VitalisDanger,
    outline              = VitalisBorder,
)

private val DarkColorScheme = darkColorScheme(
    primary              = VitalisPrimaryMuted,
    onPrimary            = Color(0xFF003826),
    primaryContainer     = VitalisPrimaryDark,
    onPrimaryContainer   = VitalisPrimaryLight,
    secondary            = VitalisPrimaryMuted,
    onSecondary          = Color(0xFF1A2B25),
    background           = Color(0xFF0D1F19),
    onBackground         = Color(0xFFD8E8E3),
    surface              = Color(0xFF1A2B25),
    onSurface            = Color(0xFFD8E8E3),
    surfaceVariant       = Color(0xFF243B33),
    onSurfaceVariant     = VitalisTextMuted,
    error                = Color(0xFFFF8A80),
    onError              = Color(0xFF690005),
)

// ─── Typography ──────────────────────────────────────────────────────────────
// Using system defaults. Add dm_sans_*.ttf / ibm_plex_mono_medium.ttf to
// res/font/ and restore the Font() references to use custom typefaces.

private val DmSans = FontFamily.Default

private val IbmPlexMono = FontFamily.Monospace

val VitalisTypography = Typography(
    displaySmall  = TextStyle(fontFamily = DmSans, fontWeight = FontWeight.Bold,    fontSize = 36.sp),
    headlineLarge = TextStyle(fontFamily = DmSans, fontWeight = FontWeight.Bold,    fontSize = 28.sp),
    headlineMedium= TextStyle(fontFamily = DmSans, fontWeight = FontWeight.SemiBold,fontSize = 24.sp),
    headlineSmall = TextStyle(fontFamily = DmSans, fontWeight = FontWeight.SemiBold,fontSize = 20.sp),
    titleLarge    = TextStyle(fontFamily = DmSans, fontWeight = FontWeight.SemiBold,fontSize = 18.sp),
    titleMedium   = TextStyle(fontFamily = DmSans, fontWeight = FontWeight.Medium,  fontSize = 16.sp),
    titleSmall    = TextStyle(fontFamily = DmSans, fontWeight = FontWeight.Medium,  fontSize = 14.sp),
    bodyLarge     = TextStyle(fontFamily = DmSans, fontWeight = FontWeight.Normal,  fontSize = 16.sp),
    bodyMedium    = TextStyle(fontFamily = DmSans, fontWeight = FontWeight.Normal,  fontSize = 14.sp),
    bodySmall     = TextStyle(fontFamily = DmSans, fontWeight = FontWeight.Normal,  fontSize = 12.sp),
    labelLarge    = TextStyle(fontFamily = DmSans, fontWeight = FontWeight.Medium,  fontSize = 14.sp),
    labelMedium   = TextStyle(fontFamily = DmSans, fontWeight = FontWeight.Medium,  fontSize = 12.sp),
    labelSmall    = TextStyle(fontFamily = DmSans, fontWeight = FontWeight.Medium,  fontSize = 11.sp),
)

/** IBM Plex Mono style — use directly for numeric metrics, scores, lab values. */
val MetricTextStyle = TextStyle(
    fontFamily = IbmPlexMono,
    fontWeight = FontWeight.Medium,
    fontSize   = 36.sp,
)

// ─── Shapes ──────────────────────────────────────────────────────────────────

val VitalisShapes = Shapes(
    extraSmall = RoundedCornerShape(6.dp),
    small      = RoundedCornerShape(10.dp),
    medium     = RoundedCornerShape(14.dp),
    large      = RoundedCornerShape(18.dp),
    extraLarge = RoundedCornerShape(24.dp),
)

// ─── Theme composable ─────────────────────────────────────────────────────────

@Composable
fun VitalisTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit
) {
    val colorScheme = if (darkTheme) DarkColorScheme else LightColorScheme

    MaterialTheme(
        colorScheme = colorScheme,
        typography  = VitalisTypography,
        shapes      = VitalisShapes,
        content     = content,
    )
}
