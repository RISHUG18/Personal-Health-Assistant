# Android API Adapter Layer — Architecture Reference
#
# This file maps every Kotlin source to its role in the clean-architecture
# stack so new contributors can orient themselves quickly.
#
# Architecture flow:
#   UI (Compose) → ViewModel → Repository → API Adapter → Retrofit → Backend
#

# ── Data Models (kotlinx.serialization) ───────────────────
app/src/main/java/com/vitalis/health/data/model/Alert.kt        # Alert, AlertEvidence, AlertsResponse
app/src/main/java/com/vitalis/health/data/model/Dashboard.kt    # DashboardData, DashboardResponse, Environment
app/src/main/java/com/vitalis/health/data/model/RagQuery.kt     # RagQueryRequest, RagData, RagResponse, Citation
app/src/main/java/com/vitalis/health/data/model/Report.kt       # ReportUploadResponse
app/src/main/java/com/vitalis/health/data/model/Doctor.kt       # Patient, PatientsResponse

# ── Network Core ──────────────────────────────────────────
app/src/main/java/com/vitalis/health/data/network/ApiResult.kt          # Sealed class (Success / Error)
app/src/main/java/com/vitalis/health/data/network/HealthApiService.kt   # Retrofit interface — raw HTTP contract

# ── API Adapter Layer ─────────────────────────────────────
app/src/main/java/com/vitalis/health/data/adapter/HealthApiAdapter.kt       # Interface
app/src/main/java/com/vitalis/health/data/adapter/HealthApiAdapterImpl.kt   # Implementation (error handling, mapping)

# ── Repository ────────────────────────────────────────────
app/src/main/java/com/vitalis/health/data/repository/HealthRepository.kt    # Business-logic layer between VM ↔ adapter

# ── DI / Network Config ──────────────────────────────────
app/src/main/java/com/vitalis/health/di/NetworkModule.kt   # OkHttp, Retrofit, Json, Adapter factory

# ── Application ───────────────────────────────────────────
app/src/main/java/com/vitalis/health/VitalisApp.kt         # App singleton — wires the graph

# ── ViewModels ────────────────────────────────────────────
app/src/main/java/com/vitalis/health/ui/DashboardViewModel.kt   # Dashboard screen state
app/src/main/java/com/vitalis/health/ui/AlertsViewModel.kt      # Alerts screen state
app/src/main/java/com/vitalis/health/ui/AssistantViewModel.kt   # AI chat screen state + history
app/src/main/java/com/vitalis/health/ui/ViewModelFactory.kt     # Manual DI factory

# ── Example UI ────────────────────────────────────────────
app/src/main/java/com/vitalis/health/ui/example/ExampleActivity.kt  # Compose Activity with 3 tabs

# ── Tests ─────────────────────────────────────────────────
app/src/test/java/com/vitalis/health/data/adapter/HealthApiAdapterImplTest.kt

# ── Build ─────────────────────────────────────────────────
app/build.gradle.kts             # Dependencies (Retrofit, OkHttp, Kotlinx Serialization, Compose)
app/src/main/AndroidManifest.xml # Permissions & launcher activity
