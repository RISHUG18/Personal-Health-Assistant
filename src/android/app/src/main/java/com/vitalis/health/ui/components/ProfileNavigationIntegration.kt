package com.vitalis.health.ui.components

import androidx.compose.runtime.Composable

/**
 * Navigation integration example for Profile Edit and Settings screens.
 *
 * This demonstrates how to integrate ProfileEditScreen and SettingsScreen
 * into your navigation graph.
 *
 * Usage in your main Activity or Navigation setup:
 *
 * ```kotlin
 * // In your Activity (e.g., ExampleActivity.kt):
 * val app = application as VitalisApp
 * val authViewModel: AuthViewModel by viewModels { app.viewModelFactory }
 * val userId = authViewModel.getUserId() ?: return
 *
 * // Navigate to Settings
 * settingsButton.setOnClickListener {
 *     setContent {
 *         SettingsScreen(
 *             viewModel = authViewModel,
 *             userId = userId,
 *             onNavigateToProfileEdit = {
 *                 // Navigate to profile edit
 *             },
 *             onNavigateToLogin = {
 *                 // Navigate back to login screen
 *             },
 *             onNavigateBack = {
 *                 // Go back to previous screen
 *             }
 *         )
 *     }
 * }
 *
 * // Navigate to Profile Edit
 * editProfileButton.setOnClickListener {
 *     // First, fetch current profile
 *     lifecycleScope.launch {
 *         when (val result = app.repository.getUserProfile(userId)) {
 *             is ApiResult.Success -> {
 *                 setContent {
 *                     ProfileEditScreen(
 *                         viewModel = authViewModel,
 *                         userId = userId,
 *                         currentProfile = result.data,
 *                         onNavigateBack = {
 *                             // Go back to previous screen
 *                         }
 *                     )
 *                 }
 *             }
 *             is ApiResult.Error -> {
 *                 // Handle error
 *             }
 *         }
 *     }
 * }
 * ```
 *
 * If using Jetpack Compose Navigation:
 *
 * ```kotlin
 * composable("settings") {
 *     SettingsScreen(
 *         viewModel = authViewModel,
 *         userId = userId,
 *         onNavigateToProfileEdit = { navController.navigate("profile_edit") },
 *         onNavigateToLogin = {
 *             navController.navigate("login") {
 *                 popUpTo("login") { inclusive = true }
 *             }
 *         },
 *         onNavigateBack = { navController.popBackStack() }
 *     )
 * }
 *
 * composable("profile_edit") {
 *     val profileState by viewModel.profileState.collectAsState()
 *     var userProfile by remember { mutableStateOf<UserProfile?>(null) }
 *
 *     LaunchedEffect(Unit) {
 *         // Fetch current profile on screen load
 *         when (val result = repository.getUserProfile(userId)) {
 *             is ApiResult.Success -> userProfile = result.data
 *             is ApiResult.Error -> {
 *                 // Handle error - maybe show a snackbar
 *             }
 *         }
 *     }
 *
 *     userProfile?.let { profile ->
 *         ProfileEditScreen(
 *             viewModel = authViewModel,
 *             userId = userId,
 *             currentProfile = profile,
 *             onNavigateBack = { navController.popBackStack() }
 *         )
 *     } ?: run {
 *         // Show loading indicator while profile is being fetched
 *         Box(
 *             modifier = Modifier.fillMaxSize(),
 *             contentAlignment = Alignment.Center
 *         ) {
 *             CircularProgressIndicator()
 *         }
 *     }
 * }
 * ```
 */
@Composable
fun ProfileNavigationIntegrationExample() {
    // This is just a documentation file.
    // See the comments above for usage examples.
}
