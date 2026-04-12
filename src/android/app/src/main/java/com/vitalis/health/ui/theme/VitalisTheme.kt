package com.vitalis.health.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Shapes
import androidx.compose.material3.Typography
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.Immutable
import androidx.compose.runtime.staticCompositionLocalOf
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.googlefonts.GoogleFont
import androidx.compose.ui.text.googlefonts.Font as GoogleFontFamilyFont
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.foundation.shape.RoundedCornerShape

// ─── Design tokens from sample.html :root ────────────────────────────────────

val VitalisPrimary       = Color(0xFF10785A)
val VitalisPrimaryDark   = Color(0xFF0B5E46)
val VitalisPrimaryDeeper = Color(0xFF084235)
val VitalisPrimaryLight  = Color(0xFFE8F5F0)
val VitalisPrimaryMuted  = Color(0xFFB4D7CC)

val VitalisAccent        = Color(0xFF1A8F6E)
val VitalisAccentWarm    = Color(0xFF2D9B7A)

val VitalisWarning       = Color(0xFFC27817)
val VitalisWarningBg     = Color(0xFFFDF6EC)
val VitalisDanger        = Color(0xFFC0392B)
val VitalisDangerBg      = Color(0xFFFDECEB)
val VitalisSuccess       = Color(0xFF1E7D5A)
val VitalisSuccessBg     = Color(0xFFE8F5F0)

val VitalisBgApp         = Color(0xFFF5F7F6)
val VitalisBgCard        = Color(0xFFFFFFFF)
val VitalisBgInput       = Color(0xFFF0F2F1)

val VitalisTextPrimary   = Color(0xFF1A2B25)
val VitalisTextSecondary = Color(0xFF506B60)
val VitalisTextMuted     = Color(0xFF8FA69B)

val VitalisBorder        = Color(0xFFDAE3DE)
val VitalisBorderLight   = Color(0xFFE8EEEB)

// Dark-mode tokens tuned for low-contrast comfort.
private val VitalisDarkPrimary       = Color(0xFF2F8D73)
private val VitalisDarkPrimaryDark   = Color(0xFF1F6B56)
private val VitalisDarkPrimaryDeeper = Color(0xFF173F35)
private val VitalisDarkPrimaryLight  = Color(0xFF204B3E)
private val VitalisDarkPrimaryMuted  = Color(0xFF7FB7A5)

private val VitalisDarkAccent        = Color(0xFF3FA487)
private val VitalisDarkAccentWarm    = Color(0xFF4CB18F)

private val VitalisDarkWarning       = Color(0xFFD49A45)
private val VitalisDarkWarningBg     = Color(0xFF3A2F1C)
private val VitalisDarkDanger        = Color(0xFFE07D72)
private val VitalisDarkDangerBg      = Color(0xFF3E2624)
private val VitalisDarkSuccess       = Color(0xFF58B890)
private val VitalisDarkSuccessBg     = Color(0xFF1E3B32)

private val VitalisDarkBgApp         = Color(0xFF121916)
private val VitalisDarkBgCard        = Color(0xFF1A2521)
private val VitalisDarkBgInput       = Color(0xFF22312B)

private val VitalisDarkTextPrimary   = Color(0xFFE3EEE8)
private val VitalisDarkTextSecondary = Color(0xFFB5C7BF)
private val VitalisDarkTextMuted     = Color(0xFF8EA29A)

private val VitalisDarkBorder        = Color(0xFF31423B)
private val VitalisDarkBorderLight   = Color(0xFF3A4E46)

// Metric-specific accent colors
val VitalisMetricSleep   = Color(0xFF6B5CE7)
val VitalisMetricSleepBg = Color(0xFFF0EEFF)
val VitalisMetricHeart   = Color(0xFFD94F4F)
val VitalisMetricHeartBg = Color(0xFFFDF0F0)
val VitalisMetricWeight  = Color(0xFF2D8BC9)
val VitalisMetricWeightBg= Color(0xFFEDF5FC)

// ─── Extended colors (not Material3 slots) ───────────────────────────────────

@Immutable
data class VitalisExtendedColors(
    val primaryDeeper: Color,
    val accent: Color,
    val accentWarm: Color,
    val surface: Color,
    val warningBg: Color,
    val dangerBg: Color,
    val successBg: Color,
    val borderLight: Color,
    val bgInput: Color,
    val bgApp: Color,
    val textPrimary: Color,
    val textMuted: Color,
    val textSecondary: Color,
    val primaryMuted: Color,
    val primaryLight: Color,
)

val LocalVitalisColors = staticCompositionLocalOf {
    VitalisExtendedColors(
        primaryDeeper = VitalisPrimaryDeeper,
        accent = VitalisAccent,
        accentWarm = VitalisAccentWarm,
        surface = VitalisBgCard,
        warningBg = VitalisWarningBg,
        dangerBg = VitalisDangerBg,
        successBg = VitalisSuccessBg,
        borderLight = VitalisBorderLight,
        bgInput = VitalisBgInput,
        bgApp = VitalisBgApp,
        textPrimary = VitalisTextPrimary,
        textMuted = VitalisTextMuted,
        textSecondary = VitalisTextSecondary,
        primaryMuted = VitalisPrimaryMuted,
        primaryLight = VitalisPrimaryLight,
    )
}

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
    errorContainer       = VitalisDangerBg,
    onErrorContainer     = VitalisDanger,
    outline              = VitalisBorder,
    outlineVariant       = VitalisBorderLight,
)

private val DarkColorScheme = darkColorScheme(
    primary              = VitalisDarkPrimary,
    onPrimary            = Color.White,
    primaryContainer     = VitalisDarkPrimaryDark,
    onPrimaryContainer   = Color(0xFFD5EADF),
    secondary            = VitalisDarkTextSecondary,
    onSecondary          = Color(0xFF0E1613),
    secondaryContainer   = VitalisDarkBgInput,
    onSecondaryContainer = VitalisDarkTextPrimary,
    background           = VitalisDarkBgApp,
    onBackground         = VitalisDarkTextPrimary,
    surface              = VitalisDarkBgCard,
    onSurface            = VitalisDarkTextPrimary,
    surfaceVariant       = VitalisDarkBgInput,
    onSurfaceVariant     = VitalisDarkTextSecondary,
    error                = VitalisDarkDanger,
    onError              = Color(0xFF220E0B),
    errorContainer       = VitalisDarkDangerBg,
    onErrorContainer     = VitalisDarkDanger,
    outline              = VitalisDarkBorder,
    outlineVariant       = VitalisDarkBorderLight,
)

// ─── Typography ──────────────────────────────────────────────────────────────

private val GoogleFontProvider = GoogleFont.Provider(
    providerAuthority = "com.google.android.gms.fonts",
    providerPackage = "com.google.android.gms",
    certificates = 0
)

private val DmSans = FontFamily(
    GoogleFontFamilyFont(
        googleFont = GoogleFont("DM Sans"),
        fontProvider = GoogleFontProvider,
        weight = FontWeight.Normal
    ),
    GoogleFontFamilyFont(
        googleFont = GoogleFont("DM Sans"),
        fontProvider = GoogleFontProvider,
        weight = FontWeight.Medium
    ),
    GoogleFontFamilyFont(
        googleFont = GoogleFont("DM Sans"),
        fontProvider = GoogleFontProvider,
        weight = FontWeight.SemiBold
    ),
    GoogleFontFamilyFont(
        googleFont = GoogleFont("DM Sans"),
        fontProvider = GoogleFontProvider,
        weight = FontWeight.Bold
    ),
)

private val IbmPlexMono = FontFamily(
    GoogleFontFamilyFont(
        googleFont = GoogleFont("IBM Plex Mono"),
        fontProvider = GoogleFontProvider,
        weight = FontWeight.Normal
    ),
    GoogleFontFamilyFont(
        googleFont = GoogleFont("IBM Plex Mono"),
        fontProvider = GoogleFontProvider,
        weight = FontWeight.Medium
    ),
    GoogleFontFamilyFont(
        googleFont = GoogleFont("IBM Plex Mono"),
        fontProvider = GoogleFontProvider,
        weight = FontWeight.Bold
    ),
)

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

/** Wellness score style: .wellness-score — 54sp, Bold, tight letter spacing */
val WellnessScoreTextStyle = TextStyle(
    fontFamily = IbmPlexMono,
    fontWeight = FontWeight.Bold,
    fontSize   = 54.sp,
    letterSpacing = (-2).sp,
)

/** Metric card value style: .metric-value — 24sp, Bold */
val MetricValueTextStyle = TextStyle(
    fontFamily = IbmPlexMono,
    fontWeight = FontWeight.Bold,
    fontSize   = 24.sp,
    letterSpacing = (-0.5).sp,
)

/** Section header: .section-header — 13sp, 700, uppercase */
val SectionHeaderStyle = TextStyle(
    fontFamily = DmSans,
    fontWeight = FontWeight.Bold,
    fontSize   = 13.sp,
    letterSpacing = 0.6.sp,
)

// ─── Shapes ──────────────────────────────────────────────────────────────────

val VitalisShapes = Shapes(
    extraSmall = RoundedCornerShape(6.dp),   // --radius-sm
    small      = RoundedCornerShape(10.dp),  // --radius-md
    medium     = RoundedCornerShape(14.dp),  // --radius-lg
    large      = RoundedCornerShape(18.dp),  // --radius-xl
    extraLarge = RoundedCornerShape(24.dp),
)

// ─── Theme composable ─────────────────────────────────────────────────────────

@Composable
fun VitalisTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit
) {
    val colorScheme = if (darkTheme) DarkColorScheme else LightColorScheme

    val extendedColors = if (darkTheme) {
        VitalisExtendedColors(
            primaryDeeper = VitalisDarkPrimaryDeeper,
            accent = VitalisDarkAccent,
            accentWarm = VitalisDarkAccentWarm,
            surface = VitalisDarkBgCard,
            warningBg = VitalisDarkWarningBg,
            dangerBg = VitalisDarkDangerBg,
            successBg = VitalisDarkSuccessBg,
            borderLight = VitalisDarkBorderLight,
            bgInput = VitalisDarkBgInput,
            bgApp = VitalisDarkBgApp,
            textPrimary = VitalisDarkTextPrimary,
            textMuted = VitalisDarkTextMuted,
            textSecondary = VitalisDarkTextSecondary,
            primaryMuted = VitalisDarkPrimaryMuted,
            primaryLight = VitalisDarkPrimaryLight,
        )
    } else {
        VitalisExtendedColors(
            primaryDeeper = VitalisPrimaryDeeper,
            accent = VitalisAccent,
            accentWarm = VitalisAccentWarm,
            surface = VitalisBgCard,
            warningBg = VitalisWarningBg,
            dangerBg = VitalisDangerBg,
            successBg = VitalisSuccessBg,
            borderLight = VitalisBorderLight,
            bgInput = VitalisBgInput,
            bgApp = VitalisBgApp,
            textPrimary = VitalisTextPrimary,
            textMuted = VitalisTextMuted,
            textSecondary = VitalisTextSecondary,
            primaryMuted = VitalisPrimaryMuted,
            primaryLight = VitalisPrimaryLight,
        )
    }

    CompositionLocalProvider(LocalVitalisColors provides extendedColors) {
        MaterialTheme(
            colorScheme = colorScheme,
            typography  = VitalisTypography,
            shapes      = VitalisShapes,
            content     = content,
        )
    }
}
