package com.statusapp.network

import android.content.Context
import android.util.Log
import com.google.firebase.auth.FirebaseAuth
import com.statusapp.config.AppConfig
import com.statusapp.engine.DerivedStatus
import kotlinx.coroutines.tasks.await
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.*
import java.util.concurrent.TimeUnit

/**
 * Retrofit API interface for backend communication.
 */
interface StatusApi {
    @POST("/device/upload-status")
    suspend fun uploadStatus(
        @Header("Authorization") auth: String,
        @Body payload: UploadStatusPayload,
    ): ApiResponse

    @POST("/device/update-fcm-token")
    suspend fun updateFCMToken(
        @Header("Authorization") auth: String,
        @Body payload: FCMTokenPayload,
    ): ApiResponse
}

data class UploadStatusPayload(
    val request_id: String,
    val owner_id: String,
    val sound_status: String,
    val movement_status: String,
    val network_status: String,
    val outdoor_status: String,
    val contact_suggestion: String?,
    val contact_methods: List<String>,
    val device_battery: Int?,
    val summary: String?,
)

data class FCMTokenPayload(
    val token: String,
)

data class ApiResponse(
    val message: String,
    val success: Boolean,
)

/**
 * API client singleton with Firebase Auth token management.
 */
class ApiClient private constructor(private val context: Context) {

    private val api: StatusApi

    init {
        val logging = HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BODY
        }

        val client = OkHttpClient.Builder()
            .addInterceptor(logging)
            .connectTimeout(10, TimeUnit.SECONDS)
            .readTimeout(10, TimeUnit.SECONDS)
            .writeTimeout(10, TimeUnit.SECONDS)
            .build()

        val retrofit = Retrofit.Builder()
            .baseUrl(AppConfig.BACKEND_URL)
            .client(client)
            .addConverterFactory(GsonConverterFactory.create())
            .build()

        api = retrofit.create(StatusApi::class.java)
    }

    /**
     * Get a fresh Firebase ID token for the currently signed-in owner.
     */
    private suspend fun getAuthToken(): String {
        val user = FirebaseAuth.getInstance().currentUser
            ?: throw IllegalStateException("No user signed in")
        val token = user.getIdToken(false).await()
        return "Bearer ${token.token}"
    }

    /**
     * Upload derived status to the backend.
     */
    suspend fun uploadStatus(requestId: String, status: DerivedStatus) {
        val auth = getAuthToken()
        val uid = FirebaseAuth.getInstance().currentUser?.uid
            ?: throw IllegalStateException("No user signed in")

        val payload = UploadStatusPayload(
            request_id = requestId,
            owner_id = uid,
            sound_status = status.soundStatus,
            movement_status = status.movementStatus,
            network_status = status.networkStatus,
            outdoor_status = status.outdoorStatus,
            contact_suggestion = status.contactSuggestion,
            contact_methods = status.contactMethods,
            device_battery = status.deviceBattery,
            summary = status.summary,
        )

        val response = api.uploadStatus(auth, payload)
        Log.d("ApiClient", "Upload response: ${response.message}")
    }

    /**
     * Update FCM token on the backend.
     */
    suspend fun updateFCMToken(token: String) {
        val auth = getAuthToken()
        api.updateFCMToken(auth, FCMTokenPayload(token))
    }

    companion object {
        @Volatile
        private var instance: ApiClient? = null

        fun getInstance(context: Context): ApiClient {
            return instance ?: synchronized(this) {
                instance ?: ApiClient(context.applicationContext).also { instance = it }
            }
        }
    }
}
