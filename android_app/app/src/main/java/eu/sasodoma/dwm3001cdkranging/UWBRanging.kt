package eu.sasodoma.dwm3001cdkranging

import android.util.Log
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.core.uwb.RangingMeasurement
import androidx.core.uwb.RangingParameters
import androidx.core.uwb.RangingPosition
import androidx.core.uwb.RangingResult
import androidx.core.uwb.UwbAddress
import androidx.core.uwb.UwbClientSessionScope
import androidx.core.uwb.UwbComplexChannel
import androidx.core.uwb.UwbDevice
import androidx.core.uwb.UwbManager
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.launch

class UWBRanging (private val uwbManager: UwbManager) {
    private lateinit var rangingJob: Job
    private var clientSession : UwbClientSessionScope? = null

    var localAdr by mutableStateOf("XX:XX")
    var rangingActive by mutableStateOf(false)
    var rangingPosition by mutableStateOf(
        RangingPosition(
            RangingMeasurement(0F),
            RangingMeasurement(0F),
            RangingMeasurement(0F),
            0L
        )
    )

    fun prepareSession(controller: Boolean) {
        CoroutineScope(Dispatchers.Main.immediate).launch {
            // Initiate a session that will be valid for a single ranging session.
            clientSession = if (controller)
                uwbManager.controllerSessionScope()
            else
                uwbManager.controleeSessionScope()
            localAdr = clientSession?.localAddress.toString()
        }
    }

    fun startRanging(remoteAdr: String): Boolean {
        if (clientSession == null) {
            return false
        }

        val remoteUwbAdr = UwbAddress(remoteAdr)

        // Create the ranging parameters.
        val partnerParameters = RangingParameters(
            uwbConfigType = RangingParameters.CONFIG_UNICAST_DS_TWR,
            // SessionKeyInfo is used to encrypt the ranging session.
            sessionKeyInfo = byteArrayOf(0x08, 0x07, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06),
            complexChannel = UwbComplexChannel(9, 9),
            peerDevices = listOf(UwbDevice(remoteUwbAdr)),
            updateRateType = RangingParameters.RANGING_UPDATE_RATE_FREQUENT,
            sessionId = 42,
            subSessionId = 0,
            subSessionKeyInfo = null
        )

        // Start a coroutine scope that initiates ranging.
        rangingJob = CoroutineScope(Dispatchers.Main.immediate).launch {
            val sessionFlow = clientSession?.prepareSession(partnerParameters)

            sessionFlow?.collect {
                when(it) {
                    is RangingResult.RangingResultPosition -> {
                        Log.d("collect", it.position.distance?.value.toString() + " m")
                        rangingPosition = it.position
                    }
                    is RangingResult.RangingResultPeerDisconnected -> {
                        Log.d("collect", "Peer disconnected")
                        stopRanging()
                    }
                }
            }
        }
        rangingActive = true
        return true
    }

    fun stopRanging() {
        if (::rangingJob.isInitialized) {
            rangingActive = false
            clientSession = null
            rangingJob.cancel()
        }
    }
}