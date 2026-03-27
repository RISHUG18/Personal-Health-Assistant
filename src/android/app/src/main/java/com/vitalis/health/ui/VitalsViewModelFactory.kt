package com.vitalis.health.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import com.vitalis.health.data.repository.HealthRepository
import com.vitalis.health.healthconnect.HealthConnectManager

/**
 * Factory for creating [VitalsViewModel] instances.
 *
 * This factory is separate from [ViewModelFactory] because [VitalsViewModel]
 * requires [HealthConnectManager] in addition to the [HealthRepository].
 */
class VitalsViewModelFactory(
    private val repository: HealthRepository,
    private val healthConnectManager: HealthConnectManager
) : ViewModelProvider.Factory {

    @Suppress("UNCHECKED_CAST")
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        if (modelClass.isAssignableFrom(VitalsViewModel::class.java)) {
            return VitalsViewModel(repository, healthConnectManager) as T
        }
        throw IllegalArgumentException("Unknown ViewModel: ${modelClass.name}")
    }
}
