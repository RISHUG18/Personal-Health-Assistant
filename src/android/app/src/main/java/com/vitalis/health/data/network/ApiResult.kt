package com.vitalis.health.data.network

/**
 * A sealed class that represents the outcome of every API call.
 *
 * Usage:
 *   when (result) {
 *       is ApiResult.Success -> use(result.data)
 *       is ApiResult.Error   -> show(result.message)
 *   }
 */
sealed class ApiResult<out T> {

    /** Successful response carrying [data]. */
    data class Success<T>(val data: T) : ApiResult<T>()

    /** Failed response carrying a human-readable [message] and optional HTTP [code]. */
    data class Error(
        val message: String,
        val code: Int? = null,
        val throwable: Throwable? = null
    ) : ApiResult<Nothing>()

    /** Convenience helpers */
    val isSuccess: Boolean get() = this is Success
    val isError: Boolean get() = this is Error

    /** Maps the data inside [Success] while preserving [Error]. */
    fun <R> map(transform: (T) -> R): ApiResult<R> = when (this) {
        is Success -> Success(transform(data))
        is Error -> this
    }

    /** Returns data or null. */
    fun getOrNull(): T? = (this as? Success)?.data

    /** Returns data or throws. */
    fun getOrThrow(): T = when (this) {
        is Success -> data
        is Error -> throw throwable ?: RuntimeException(message)
    }
}
