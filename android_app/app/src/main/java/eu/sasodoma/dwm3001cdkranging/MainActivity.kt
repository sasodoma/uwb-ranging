package eu.sasodoma.dwm3001cdkranging

import android.Manifest
import android.content.pm.PackageManager
import android.os.Bundle
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.Checkbox
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextField
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.core.uwb.UwbManager
import eu.sasodoma.dwm3001cdkranging.ui.theme.DWM3001CDKRangingTheme

class MainActivity : ComponentActivity() {
    /* Get the UWB_RANGING permission */
    private val permissionRequester = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { isGranted -> if (!isGranted) requestPermission() }

    private fun requestPermission() {
        permissionRequester.launch(Manifest.permission.UWB_RANGING)
    }

    private lateinit var uwbManager : UwbManager
    private lateinit var uwbRanging : UWBRanging

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Get the permission if not granted
        if (checkSelfPermission(Manifest.permission.UWB_RANGING) != PackageManager.PERMISSION_GRANTED) {
            requestPermission()
        }

        uwbManager = UwbManager.createInstance(this)
        uwbRanging = UWBRanging(uwbManager)

        enableEdgeToEdge()
        setContent {
            DWM3001CDKRangingTheme {
                Scaffold(
                    modifier = Modifier.fillMaxSize(),
                    topBar = {AppBar()}
                ) { padding ->
                    MainScreen(padding)
                }
            }
        }
    }

    @OptIn(ExperimentalMaterial3Api::class)
    @Composable
    fun AppBar() {
        TopAppBar(
            title = { Text("DWM3001CDK Ranging") },
            colors = TopAppBarDefaults.topAppBarColors(
                containerColor = MaterialTheme.colorScheme.primary,
                titleContentColor = MaterialTheme.colorScheme.onPrimary
            )
        )
    }

    @Composable
    fun MainScreen(paddingValues: PaddingValues) {
        Column (
            modifier = Modifier
                .padding(paddingValues)
                .padding(top = 16.dp)
                .fillMaxWidth(),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            PrepareSession()
            LocalAddr()

            StartStopRanging()
            PositionText()
        }
    }

    @Composable
    fun PrepareSession() {
        var checked by remember { mutableStateOf(false) }
        Row( verticalAlignment = Alignment.CenterVertically ) {
            Text("Controller")
            Checkbox(
                checked = checked,
                onCheckedChange = { checked = it }
            )
        }
        Button(
            onClick = {
                if (uwbRanging.rangingActive) {
                    Toast.makeText(
                        this@MainActivity,
                        "Ranging session active!",
                        Toast.LENGTH_SHORT
                    ).show()
                } else {
                    uwbRanging.prepareSession(checked)
                }
            }
        ) {
            Text("Prepare session")
        }
    }

    @Composable
    fun LocalAddr() {
        Text("Local address: ${uwbRanging.localAdr}")
    }

    @Composable
    fun StartStopRanging() {
        var destinationAddress by remember { mutableStateOf("00:00") }
        Text("Destination address:")
        TextField(
            value = destinationAddress,
            onValueChange = { value -> destinationAddress = value.uppercase() },
            placeholder = { Text("00:00") }
        )
        if (uwbRanging.rangingActive) {
            Button(
                onClick = { uwbRanging.stopRanging() }
            ) {
                Text("Stop Ranging")
            }
        } else {
            Button(
                onClick = {
                    val pattern = "[0-9A-F]{2}:[0-9A-F]{2}"
                    if (destinationAddress.matches(pattern.toRegex())) {
                        if (!uwbRanging.startRanging(destinationAddress)) {
                            Toast.makeText(
                                this@MainActivity,
                                "Session not initialized!",
                                Toast.LENGTH_SHORT
                            ).show()
                        }
                    } else {
                        Toast.makeText(
                            this@MainActivity,
                            "Invalid address format",
                            Toast.LENGTH_SHORT
                        ).show()
                    }
                }
            ) {
                Text("Start Ranging")
            }
        }
    }

    @Composable
    fun PositionText() {
        val position = uwbRanging.rangingPosition
        Text("Distance: ${position.distance?.value} m")
        Text("Azimuth: ${position.azimuth?.value} °")
        Text("Elevation: ${position.elevation?.value} °")
        Text("Elapsed time: ${position.elapsedRealtimeNanos} ns")
    }
}