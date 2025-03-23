# UWB Ranging with DWM3001CDK and Android
This repository contains basic code required to do ranging between the Qorvo DWM3001CDK and an Android phone. There is no Bluetooth implementation, out-of-band communication is done manually and the DWM3001CDK needs to be connected to a computer via USB to start ranging.

## Android app
The `android_app` directory contains a simple UWB project that is capable of starting and stopping a ranging session and displaying the resulting data.

Tested on:
- Pixel 8 Pro
- Pixel 9 Pro

## Python script
The `new_python_script` directory contains a copy of the script found in the [DW3_QM33_SDK_1.0.2.zip](https://github.com/sasodoma/uwb-ranging/releases/tag/v2.0.0) archive provided by Qorvo. It is modified slightly to work with the Android app. The modifications are listed below:
- `--ranging-span` default changed to 120 to match Android config
- `--mac` and `--dest-mac` parameters modified to accept the MAC address in the format `XX:XX`
- `--en-rssi` default changed to True to match Android config
- `--preabmle-idx` default changed to 9 to match Android config
- `--slots-per-rr` default changed to 6 to match Android config
- `--hopping-mode` default changed to `enabled` to match Android config

## Firmware
The Python script uses the new UCI firmware from the above archive, a copy is also provided in the `new_firmware` directory.

## Usage
To setup the environment:
- Install the Android app (.apk provided in releases)
- Flash the firmware using J-Link and connect the module to the PC using the other USB port
- **[OPTIONAL]** create and activate a virtual environment in the `new_python_script` directory.
- Install the python requirements using `pip install -r requirements.txt`

To perform a ranging session:
- Open the Android app, select if you want the phone to be a controller or controlee (with this new firmware, the ranging appears to work reliably with both options)
- Press the `Prepare session` button to get the phone's local address
- Launch `run_fira_twr.py`, use the correct port for `-p` and the address from the previous step for `--dest-mac`, optionally use the `--controlee` flag
```shell
python run_fira_twr.py -p <COMX> --mac 00:00 --dest-mac <XX:XX> [--controlee]
```
- Press `Start ranging` on the phone

<br><br>

# OLD FIRMWARE
This section refers to the old firmware that is no longer available from Qorvo.
It is found in the `firmware` directory and can be used with the script in the `python_script` directory.

## Python script
The `python_script` directory contains a copy of the script found in the [DWM3001CDK DK Software, Sources, Tools and Developer Guide.zip](https://github.com/sasodoma/uwb-ranging/releases/tag/v1.0.1) archive provided by Qorvo. It is modified slightly to work with Android. The modifications are listed below:
- `App.RangingInterval` is set to 120 to match Android config
- `App.SlotsPerRr` is set to 6 to match Android config
- `App.HoppingMode` is set to 1 to match Android config
- Added command line parameters `address` and `target` to set the local and target MAC address from the command line. The input format is XX:XX. Note that the script reverses the byte order, because the Python library accepts the address as a value instead of an array.

## Firmware
The Python script uses UCI firmware from the above archive, a copy is also provided in the `firmware` directory.

## Usage
To setup the environment:
- Install the Android app (.apk provided in releases)
- Flash the firmware using J-Link and connect the module to the PC using the other USB port
- **[OPTIONAL]** create and activate a virtual environment in the `python_script` directory.
- Install the python requirements using `pip install -r requirements.txt`

To perform a ranging session:
- Open the Android app, select if you want the phone to be a controller or controlee (note that right now, for unknown reasons, the ranging only works reliably if the phone is controlee)
- Press the `Prepare session` button to get the phone's local address
- Launch `uci_uart_fira_test.py`, use the correct port for `-p` and the address from the previous step for `-t`, optionally use the `--controlee` flag
```shell
python uci_uart_fira_test.py -p <COMX> -a 00:00 -t <XX:XX> [--controlee]
```
- Press `Start ranging` on the phone
