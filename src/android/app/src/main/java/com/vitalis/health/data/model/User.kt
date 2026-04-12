package com.vitalis.health.data.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

// ─────────────────────────────────────────────
// User Profile Models
// ─────────────────────────────────────────────

/**
 * User profile response from GET /api/v1/users/{user_id}.
 * Contains user information for dashboard greeting and profile display.
 */
@Serializable
data class UserProfile(
    val id: String,
    val email: String,
    @SerialName("full_name")
    val fullName: String,
    val phone: String? = null,
    @SerialName("date_of_birth")
    val dateOfBirth: String? = null,
    val gender: String? = null,
    val city: String? = null,
    val state: String? = null,
    val country: String? = null,
    @SerialName("blood_group")
    val bloodGroup: String? = null,
    @SerialName("height_cm")
    val heightCm: Double? = null,
    @SerialName("weight_kg")
    val weightKg: Double? = null,
    @SerialName("is_active")
    val isActive: Boolean = true,
    @SerialName("created_at")
    val createdAt: String? = null
)

/**
 * Request payload for PATCH /api/v1/users/{user_id}.
 * All fields are optional — only include fields to be updated.
 */
@Serializable
data class UserUpdateRequest(
    @SerialName("full_name")
    val fullName: String?,
    val phone: String?,
    @SerialName("date_of_birth")
    val dateOfBirth: String?,
    val gender: String?,
    val city: String?,
    val state: String?,
    val country: String?,
    @SerialName("blood_group")
    val bloodGroup: String?,
    @SerialName("height_cm")
    val heightCm: Double?,
    @SerialName("weight_kg")
    val weightKg: Double?
)
