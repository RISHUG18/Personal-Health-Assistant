package com.vitalis.health.data.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

/**
 * Request body for POST /auth/login
 */
@Serializable
data class UserLoginRequest(
    @SerialName("email")
    val email: String,
    @SerialName("password")
    val password: String
)

/**
 * Request body for POST /auth/register
 */
@Serializable
data class UserRegisterRequest(
    @SerialName("email")
    val email: String,
    @SerialName("password")
    val password: String,
    @SerialName("full_name")
    val fullName: String,
    @SerialName("date_of_birth")
    val dateOfBirth: String,
    @SerialName("gender")
    val gender: String? = null,
    @SerialName("height_cm")
    val heightCm: Double? = null,
    @SerialName("weight_kg")
    val weightKg: Double? = null,
    // Kept for backward compatibility where backend auth schema still expects age.
    @SerialName("age")
    val age: Int? = null,
    @SerialName("role")
    val role: String = "patient"
)

/**
 * Response from both /auth/login and /auth/register endpoints
 */
@Serializable
data class AuthResponse(
    @SerialName("message")
    val message: String,
    @SerialName("user_id")
    val userId: String,
    @SerialName("access_token")
    val accessToken: String,
    @SerialName("refresh_token")
    val refreshToken: String
)
