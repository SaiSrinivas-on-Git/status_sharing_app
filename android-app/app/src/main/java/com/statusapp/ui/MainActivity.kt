package com.statusapp.ui

import android.Manifest
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.util.Log
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.google.firebase.auth.FirebaseAuth
import com.google.firebase.auth.GoogleAuthProvider
import com.google.firebase.messaging.FirebaseMessaging
import com.statusapp.network.ApiClient
import kotlinx.coroutines.launch
import kotlinx.coroutines.tasks.await
import com.google.android.gms.auth.api.signin.GoogleSignIn
import com.google.android.gms.auth.api.signin.GoogleSignInOptions
import com.google.android.gms.common.api.ApiException

private const val TAG = "MainActivity"

class MainActivity : ComponentActivity() {

    private val auth = FirebaseAuth.getInstance()

    // Permission launcher
    private val permissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { results ->
        val allGranted = results.all { it.value }
        if (allGranted) {
            Log.d(TAG, "All permissions granted")
        } else {
            Log.w(TAG, "Some permissions denied: ${results.filter { !it.value }.keys}")
            Toast.makeText(this, "Some permissions were denied — status collection may be limited", Toast.LENGTH_LONG).show()
        }
    }

    // Google Sign-In launcher
    private val signInLauncher = registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) { result ->
        val task = GoogleSignIn.getSignedInAccountFromIntent(result.data)
        try {
            val account = task.getResult(ApiException::class.java)
            account?.idToken?.let { firebaseAuthWithGoogle(it) }
        } catch (e: ApiException) {
            Log.e(TAG, "Google sign-in failed", e)
            Toast.makeText(this, "Sign-in failed", Toast.LENGTH_SHORT).show()
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        requestPermissions()

        setContent {
            StatusAppTheme {
                val user = auth.currentUser
                var isSignedIn by remember { mutableStateOf(user != null) }
                var fcmToken by remember { mutableStateOf<String?>(null) }

                // Get FCM token
                LaunchedEffect(isSignedIn) {
                    if (isSignedIn) {
                        try {
                            val token = FirebaseMessaging.getInstance().token.await()
                            fcmToken = token
                            Log.d(TAG, "FCM Token: ${token.take(20)}...")

                            // Upload token to backend
                            ApiClient.getInstance(applicationContext).updateFCMToken(token)
                        } catch (e: Exception) {
                            Log.e(TAG, "Failed to get/upload FCM token", e)
                        }
                    }
                }

                if (isSignedIn) {
                    OwnerHomeScreen(
                        email = auth.currentUser?.email ?: "Unknown",
                        fcmToken = fcmToken,
                        onSignOut = {
                            auth.signOut()
                            isSignedIn = false
                        }
                    )
                } else {
                    LoginScreen(
                        onSignIn = { signInWithGoogle() },
                        onSignedIn = { isSignedIn = true }
                    )
                }
            }
        }
    }

    private fun signInWithGoogle() {
        val gso = GoogleSignInOptions.Builder(GoogleSignInOptions.DEFAULT_SIGN_IN)
            .requestIdToken("YOUR_WEB_CLIENT_ID") // Replace with your Firebase Web Client ID
            .requestEmail()
            .build()

        val client = GoogleSignIn.getClient(this, gso)
        signInLauncher.launch(client.signInIntent)
    }

    private fun firebaseAuthWithGoogle(idToken: String) {
        val credential = GoogleAuthProvider.getCredential(idToken, null)
        auth.signInWithCredential(credential)
            .addOnCompleteListener(this) { task ->
                if (task.isSuccessful) {
                    Log.d(TAG, "Firebase auth success")
                    // Recreate to refresh state
                    recreate()
                } else {
                    Log.e(TAG, "Firebase auth failed", task.exception)
                    Toast.makeText(this, "Authentication failed", Toast.LENGTH_SHORT).show()
                }
            }
    }

    private fun requestPermissions() {
        val permissions = mutableListOf(
            Manifest.permission.ACCESS_FINE_LOCATION,
            Manifest.permission.ACCESS_COARSE_LOCATION,
        )

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            permissions.add(Manifest.permission.ACTIVITY_RECOGNITION)
        }

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            permissions.add(Manifest.permission.POST_NOTIFICATIONS)
        }

        val needed = permissions.filter {
            checkSelfPermission(it) != PackageManager.PERMISSION_GRANTED
        }

        if (needed.isNotEmpty()) {
            permissionLauncher.launch(needed.toTypedArray())
        }
    }
}

// ═══════════════════════════════════════════════════════════════════
// COMPOSE UI
// ═══════════════════════════════════════════════════════════════════

@Composable
fun StatusAppTheme(content: @Composable () -> Unit) {
    val darkColors = darkColorScheme(
        primary = Color(0xFF6366F1),
        onPrimary = Color.White,
        surface = Color(0xFF111127),
        background = Color(0xFF0A0A1A),
        onSurface = Color(0xFFF0F0F8),
        onBackground = Color(0xFFF0F0F8),
        surfaceVariant = Color(0xFF1A1A3A),
    )

    MaterialTheme(
        colorScheme = darkColors,
        content = content
    )
}

@Composable
fun LoginScreen(onSignIn: () -> Unit, onSignedIn: () -> Unit) {
    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(
                Brush.radialGradient(
                    colors = listOf(
                        Color(0xFF6366F1).copy(alpha = 0.1f),
                        Color(0xFF0A0A1A)
                    ),
                    radius = 800f,
                )
            ),
        contentAlignment = Alignment.Center,
    ) {
        Card(
            modifier = Modifier
                .padding(32.dp)
                .fillMaxWidth(),
            shape = RoundedCornerShape(24.dp),
            colors = CardDefaults.cardColors(
                containerColor = Color(0xFF111127).copy(alpha = 0.9f)
            ),
        ) {
            Column(
                modifier = Modifier.padding(32.dp),
                horizontalAlignment = Alignment.CenterHorizontally,
            ) {
                Icon(
                    imageVector = Icons.Default.Sensors,
                    contentDescription = "Status",
                    tint = Color(0xFF6366F1),
                    modifier = Modifier.size(56.dp),
                )
                Spacer(modifier = Modifier.height(16.dp))
                Text(
                    text = "Status App",
                    fontSize = 28.sp,
                    fontWeight = FontWeight.Bold,
                    color = Color(0xFF6366F1),
                )
                Text(
                    text = "Owner Device",
                    fontSize = 14.sp,
                    color = Color(0xFFA0A0C0),
                )
                Spacer(modifier = Modifier.height(32.dp))
                Button(
                    onClick = onSignIn,
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(12.dp),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = Color(0xFF6366F1)
                    ),
                ) {
                    Text("Sign in with Google", modifier = Modifier.padding(8.dp))
                }
                Spacer(modifier = Modifier.height(12.dp))
                Text(
                    text = "Sign in as the device owner to enable status sharing",
                    fontSize = 12.sp,
                    color = Color(0xFF606080),
                    textAlign = TextAlign.Center,
                )
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun OwnerHomeScreen(email: String, fcmToken: String?, onSignOut: () -> Unit) {
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Status App") },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = Color(0xFF111127),
                    titleContentColor = Color(0xFFF0F0F8),
                ),
                actions = {
                    IconButton(onClick = onSignOut) {
                        Icon(Icons.Default.Logout, "Sign out", tint = Color(0xFFA0A0C0))
                    }
                },
            )
        },
        containerColor = Color(0xFF0A0A1A),
    ) { padding ->
        Column(
            modifier = Modifier
                .padding(padding)
                .padding(24.dp)
                .verticalScroll(rememberScrollState()),
        ) {
            // Status indicator
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(16.dp),
                colors = CardDefaults.cardColors(
                    containerColor = Color(0xFF10B981).copy(alpha = 0.1f)
                ),
            ) {
                Row(
                    modifier = Modifier.padding(20.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Icon(
                        Icons.Default.CheckCircle,
                        "Active",
                        tint = Color(0xFF10B981),
                        modifier = Modifier.size(32.dp),
                    )
                    Spacer(modifier = Modifier.width(16.dp))
                    Column {
                        Text(
                            "Device Active",
                            fontWeight = FontWeight.Bold,
                            color = Color(0xFF10B981),
                        )
                        Text(
                            "Ready to respond to status requests",
                            fontSize = 13.sp,
                            color = Color(0xFFA0A0C0),
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(20.dp))

            // Info cards
            InfoCard("Signed in as", email, Icons.Default.AccountCircle)
            Spacer(modifier = Modifier.height(12.dp))

            InfoCard(
                "FCM Token",
                if (fcmToken != null) "${fcmToken.take(30)}..." else "Fetching...",
                Icons.Default.Notifications,
            )
            Spacer(modifier = Modifier.height(12.dp))

            InfoCard(
                "How it works",
                "This app runs in the background. When a viewer checks your status, " +
                    "the backend sends a push notification, and this app automatically " +
                    "collects your device state and uploads a privacy-safe status.",
                Icons.Default.Info,
            )

            Spacer(modifier = Modifier.height(24.dp))

            Text(
                text = "Keep this app installed and signed in. No further action needed.",
                fontSize = 13.sp,
                color = Color(0xFF606080),
                textAlign = TextAlign.Center,
                modifier = Modifier.fillMaxWidth(),
            )
        }
    }
}

@Composable
fun InfoCard(title: String, value: String, icon: androidx.compose.ui.graphics.vector.ImageVector) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(
            containerColor = Color(0xFF1A1A3A).copy(alpha = 0.6f)
        ),
    ) {
        Row(
            modifier = Modifier.padding(16.dp),
            verticalAlignment = Alignment.Top,
        ) {
            Icon(
                icon,
                title,
                tint = Color(0xFF6366F1),
                modifier = Modifier.size(24.dp),
            )
            Spacer(modifier = Modifier.width(12.dp))
            Column {
                Text(
                    title,
                    fontSize = 12.sp,
                    fontWeight = FontWeight.SemiBold,
                    color = Color(0xFF606080),
                )
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    value,
                    fontSize = 14.sp,
                    color = Color(0xFFF0F0F8),
                )
            }
        }
    }
}
