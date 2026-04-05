package com.vitalis.health.ui

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.vitalis.health.ui.theme.VitalisTextSecondary
import com.vitalis.health.ui.theme.VitalisTheme

/**
 * Activity to display the Health Connect privacy policy.
 *
 * This activity is required by Health Connect for the permission rationale
 * intent filter declared in the manifest.
 */
class PrivacyPolicyActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        setContent {
            VitalisTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    Column(
                        modifier = Modifier
                            .fillMaxSize()
                            .padding(24.dp)
                            .verticalScroll(rememberScrollState()),
                        verticalArrangement = Arrangement.spacedBy(16.dp)
                    ) {
                        Text(
                            text = "Suryaquantum AI Health Data Privacy Policy",
                            style = MaterialTheme.typography.headlineMedium,
                            fontWeight = FontWeight.Bold
                        )

                        Spacer(modifier = Modifier.height(8.dp))

                        PolicySection(
                            title = "Data We Collect",
                            content = """
                                Suryaquantum AI collects the following health data from Health Connect with your permission:
                                • Heart rate and resting heart rate measurements
                                • Heart rate variability (HRV)
                                • Step count and active minutes
                                • Sleep duration and sleep stages
                                • Blood oxygen saturation (SpO2)
                                • Calories burned
                            """.trimIndent()
                        )

                        PolicySection(
                            title = "How We Use Your Data",
                            content = """
                                We use your health data to:
                                • Display your health metrics in the app
                                • Track trends in your health over time
                                • Provide personalized health insights via our AI assistant
                                • Generate health alerts based on abnormal readings
                                • Sync with your healthcare providers (when authorized)
                            """.trimIndent()
                        )

                        PolicySection(
                            title = "Data Storage & Security",
                            content = """
                                • Your health data is encrypted in transit and at rest
                                • Data is stored securely on our servers
                                • We implement industry-standard security measures
                                • Your data is never sold to third parties
                            """.trimIndent()
                        )

                        PolicySection(
                            title = "Data Sharing",
                            content = """
                                We only share your health data:
                                • With healthcare providers you explicitly authorize
                                • With our AI service for generating health insights (anonymized)
                                • When required by law or legal process
                            """.trimIndent()
                        )

                        PolicySection(
                            title = "Your Rights",
                            content = """
                                You have the right to:
                                • Revoke Health Connect permissions at any time
                                • Request deletion of your health data
                                • Export your health data
                                • Know what data we collect and how it's used
                            """.trimIndent()
                        )

                        PolicySection(
                            title = "Contact Us",
                            content = """
                                If you have questions about this privacy policy or your health data, please contact us at:
                                privacy@vitalis.health
                            """.trimIndent()
                        )

                        Spacer(modifier = Modifier.height(24.dp))

                        Text(
                            text = "Last updated: March 2026",
                            style = MaterialTheme.typography.bodySmall,
                            color = VitalisTextSecondary
                        )
                    }
                }
            }
        }
    }
}

@androidx.compose.runtime.Composable
private fun PolicySection(title: String, content: String) {
    Column {
        Text(
            text = title,
            style = MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.SemiBold
        )
        Spacer(modifier = Modifier.height(8.dp))
        Text(
            text = content,
            style = MaterialTheme.typography.bodyMedium,
            color = VitalisTextSecondary
        )
    }
}
