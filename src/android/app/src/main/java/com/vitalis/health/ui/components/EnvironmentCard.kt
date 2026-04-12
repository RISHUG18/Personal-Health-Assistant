package com.vitalis.health.ui.components

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Air
import androidx.compose.material.icons.outlined.Cloud
import androidx.compose.material.icons.outlined.LocationOn
import androidx.compose.material.icons.outlined.Thermostat
import androidx.compose.material.icons.outlined.WaterDrop
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.vitalis.health.data.model.EnvironmentData
import com.vitalis.health.ui.theme.LocalVitalisColors
import com.vitalis.health.ui.theme.MetricValueTextStyle
import com.vitalis.health.ui.theme.VitalisBgInput
import com.vitalis.health.ui.theme.VitalisDanger
import com.vitalis.health.ui.theme.VitalisPrimary
import com.vitalis.health.ui.theme.VitalisAccentWarm
import com.vitalis.health.ui.theme.VitalisSuccess
import com.vitalis.health.ui.theme.VitalisTextMuted
import com.vitalis.health.ui.theme.VitalisTextSecondary
import com.vitalis.health.ui.theme.VitalisWarning

/**
 * Environment card displaying AQI and weather data.
 *
 * Features:
 * - AQI level with color-coded severity
 * - Temperature, humidity, and weather condition
 * - Location display
 * - Loading and permission states
 *
 * @param environmentData The environment data to display, or null if not loaded
 * @param isLoading Whether environment data is currently loading
 * @param onRequestPermission Callback when user taps to grant location permission
 * @param locationAvailable Whether location data is available
 * @param modifier Optional modifier
 */
@Composable
fun EnvironmentCard(
    environmentData: EnvironmentData?,
    isLoading: Boolean = false,
    locationAvailable: Boolean = true,
    onRequestPermission: (() -> Unit)? = null,
    modifier: Modifier = Modifier
) {
    val colors = LocalVitalisColors.current

    Card(
        modifier = modifier.fillMaxWidth(),
        shape = MaterialTheme.shapes.large,
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surface
        ),
        border = BorderStroke(1.dp, colors.borderLight),
        elevation = CardDefaults.cardElevation(defaultElevation = 0.dp)
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(bottom = 16.dp)
        ) {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(3.dp)
                    .background(
                        Brush.horizontalGradient(
                            colors = listOf(VitalisPrimary, VitalisAccentWarm)
                        )
                    )
            )

            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(16.dp)
            ) {
            // Header
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "Environment",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.SemiBold,
                    color = MaterialTheme.colorScheme.onSurface
                )

                // Location badge
                environmentData?.locationCity?.let { city ->
                    LocationBadge(city = city)
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            when {
                isLoading -> {
                    // Loading state
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(100.dp),
                        contentAlignment = Alignment.Center
                    ) {
                        CircularProgressIndicator(
                            color = VitalisPrimary,
                            strokeWidth = 2.dp,
                            modifier = Modifier.size(32.dp)
                        )
                    }
                }
                !locationAvailable || environmentData == null -> {
                    // No location / permission required
                    LocationPermissionPrompt(onRequestPermission = onRequestPermission)
                }
                else -> {
                    // Show environment data
                    EnvironmentContent(data = environmentData)
                }
            }
            }
        }
    }
}

@Composable
private fun LocationBadge(
    city: String,
    modifier: Modifier = Modifier
) {
    Surface(
        modifier = modifier,
        shape = RoundedCornerShape(6.dp),
        color = VitalisBgInput
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Icon(
                imageVector = Icons.Outlined.LocationOn,
                contentDescription = null,
                tint = VitalisTextSecondary,
                modifier = Modifier.size(14.dp)
            )
            Spacer(modifier = Modifier.width(4.dp))
            Text(
                text = city,
                style = MaterialTheme.typography.labelSmall,
                color = VitalisTextSecondary
            )
        }
    }
}

@Composable
private fun LocationPermissionPrompt(
    onRequestPermission: (() -> Unit)?,
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier.fillMaxWidth(),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Icon(
            imageVector = Icons.Outlined.LocationOn,
            contentDescription = null,
            tint = VitalisTextMuted,
            modifier = Modifier.size(40.dp)
        )

        Spacer(modifier = Modifier.height(8.dp))

        Text(
            text = "Location required",
            style = MaterialTheme.typography.bodyMedium,
            color = VitalisTextSecondary
        )

        Text(
            text = "Enable location to see local AQI and weather",
            style = MaterialTheme.typography.bodySmall,
            color = VitalisTextMuted
        )

        if (onRequestPermission != null) {
            Spacer(modifier = Modifier.height(8.dp))

            TextButton(onClick = onRequestPermission) {
                Text(
                    text = "Enable Location",
                    color = VitalisPrimary
                )
            }
        }
    }
}

@Composable
private fun EnvironmentContent(
    data: EnvironmentData,
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        // AQI Section (prominent display)
        data.aqiLevel?.let { aqi ->
            AqiDisplay(aqiLevel = aqi)
        }

        // Weather metrics row
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceEvenly
        ) {
            // Temperature
            data.temperatureCelsius?.let { temp ->
                WeatherMetric(
                    icon = Icons.Outlined.Thermostat,
                    value = "${temp.toInt()}°C",
                    label = "Temperature"
                )
            }

            // Humidity
            data.humidityPercent?.let { humidity ->
                WeatherMetric(
                    icon = Icons.Outlined.WaterDrop,
                    value = "${humidity.toInt()}%",
                    label = "Humidity"
                )
            }

            // Weather condition
            data.weatherCondition?.let { condition ->
                WeatherMetric(
                    icon = Icons.Outlined.Cloud,
                    value = condition,
                    label = "Condition"
                )
            }
        }
    }
}

@Composable
private fun AqiDisplay(
    aqiLevel: Int,
    modifier: Modifier = Modifier
) {
    val (aqiColor, aqiLabel, aqiDescription) = getAqiInfo(aqiLevel)

    Surface(
        modifier = modifier.fillMaxWidth(),
        shape = RoundedCornerShape(12.dp),
        color = aqiColor.copy(alpha = 0.1f)
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            // AQI Icon
            Box(
                modifier = Modifier
                    .size(48.dp)
                    .clip(RoundedCornerShape(12.dp))
                    .background(aqiColor.copy(alpha = 0.15f)),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = Icons.Outlined.Air,
                    contentDescription = null,
                    tint = aqiColor,
                    modifier = Modifier.size(24.dp)
                )
            }

            Spacer(modifier = Modifier.width(16.dp))

            // AQI Info
            Column(modifier = Modifier.weight(1f)) {
                Row(
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "AQI",
                        style = MaterialTheme.typography.bodySmall,
                        color = VitalisTextSecondary
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    AqiBadge(label = aqiLabel, color = aqiColor)
                }

                Spacer(modifier = Modifier.height(4.dp))

                Text(
                    text = aqiDescription,
                    style = MaterialTheme.typography.bodySmall,
                    color = VitalisTextMuted
                )
            }

            // AQI Value
            Text(
                text = aqiLevel.toString(),
                style = MetricValueTextStyle,
                color = aqiColor
            )
        }
    }
}

@Composable
private fun AqiBadge(
    label: String,
    color: Color,
    modifier: Modifier = Modifier
) {
    Surface(
        modifier = modifier,
        shape = RoundedCornerShape(4.dp),
        color = color.copy(alpha = 0.2f)
    ) {
        Text(
            text = label,
            style = MaterialTheme.typography.labelSmall,
            fontWeight = FontWeight.SemiBold,
            color = color,
            maxLines = 1,
            overflow = TextOverflow.Ellipsis,
            modifier = Modifier.padding(horizontal = 8.dp, vertical = 3.dp)
        )
    }
}

@Composable
private fun WeatherMetric(
    icon: ImageVector,
    value: String,
    label: String,
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier,
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Icon(
            imageVector = icon,
            contentDescription = null,
            tint = VitalisTextSecondary,
            modifier = Modifier.size(20.dp)
        )

        Spacer(modifier = Modifier.height(4.dp))

        Text(
            text = value,
            style = MetricValueTextStyle.copy(fontSize = MaterialTheme.typography.bodyLarge.fontSize),
            fontWeight = FontWeight.Medium,
            color = MaterialTheme.colorScheme.onSurface
        )

        Text(
            text = label,
            style = MaterialTheme.typography.labelSmall,
            color = VitalisTextMuted
        )
    }
}

/**
 * Returns AQI color, label, and description based on the AQI level.
 * Based on EPA Air Quality Index standards.
 */
private fun getAqiInfo(aqiLevel: Int): Triple<Color, String, String> {
    return when {
        aqiLevel <= 50 -> Triple(
            VitalisSuccess,
            "Good",
            "Air quality is satisfactory"
        )
        aqiLevel <= 100 -> Triple(
            VitalisPrimary,
            "Moderate",
            "Acceptable quality for most"
        )
        aqiLevel <= 150 -> Triple(
            VitalisWarning,
            "Sensitive Groups",
            "Sensitive groups may be affected"
        )
        aqiLevel <= 200 -> Triple(
            VitalisWarning,
            "Unhealthy",
            "Everyone may experience effects"
        )
        aqiLevel <= 300 -> Triple(
            VitalisDanger,
            "Very Unhealthy",
            "Health alert: serious effects"
        )
        else -> Triple(
            VitalisDanger,
            "Hazardous",
            "Health emergency conditions"
        )
    }
}
