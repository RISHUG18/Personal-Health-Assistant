package com.vitalis.health.di

import com.jakewharton.retrofit2.converter.kotlinx.serialization.asConverterFactory
import com.vitalis.health.data.adapter.HealthApiAdapter
import com.vitalis.health.data.adapter.HealthApiAdapterImpl
import com.vitalis.health.data.local.TokenManager
import com.vitalis.health.data.network.HealthApiService
import kotlinx.serialization.ExperimentalSerializationApi
import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import java.util.concurrent.TimeUnit

/**
 * Manual dependency-injection module.
 *
 * In a production app this would be replaced by Hilt / Koin.  For now it
 * provides a single source of truth for the network stack so no class ever
 * creates its own Retrofit instance.
 *
 * Usage:
 *   val adapter = NetworkModule.provideAdapter("http://10.0.2.2:8000", tokenManager)
 */
object NetworkModule {

    /** Lenient JSON parser — ignores unknown keys from the backend. */
    @OptIn(ExperimentalSerializationApi::class)
    val json: Json = Json {
        ignoreUnknownKeys = true
        isLenient = true
        coerceInputValues = true
        explicitNulls = false
    }

    /** Shared OkHttp client with logging in debug builds. */
    fun provideOkHttpClient(tokenManager: TokenManager? = null): OkHttpClient {
        val vitalis = VitalisInterceptor(tokenManager)
        val logging = HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BODY
        }
        return OkHttpClient.Builder()
            .addInterceptor(vitalis)
            .addInterceptor(logging)
            .connectTimeout(30, TimeUnit.SECONDS)
            .readTimeout(30, TimeUnit.SECONDS)
            .writeTimeout(60, TimeUnit.SECONDS)
            .build()
    }

    /** Retrofit instance configured with Kotlinx Serialization. */
    fun provideRetrofit(
        baseUrl: String,
        client: OkHttpClient
    ): Retrofit {
        return Retrofit.Builder()
            .baseUrl(baseUrl)
            .client(client)
            .addConverterFactory(json.asConverterFactory("application/json".toMediaType()))
            .build()
    }

    /** The raw Retrofit service interface. */
    fun provideApiService(retrofit: Retrofit): HealthApiService =
        retrofit.create(HealthApiService::class.java)

    /**
     * The single adapter instance the rest of the app should use.
     *
     * @param baseUrl       Base URL of the backend (e.g. BuildConfig.BASE_URL)
     * @param tokenManager  TokenManager for auth header injection
     */
    fun provideAdapter(baseUrl: String, tokenManager: TokenManager? = null): HealthApiAdapter {
        val client = provideOkHttpClient(tokenManager)
        val retrofit = provideRetrofit(baseUrl, client)
        val service = provideApiService(retrofit)
        return HealthApiAdapterImpl(service)
    }
}
