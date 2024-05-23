# UWB Ranging with DWM3001CDK and Pixel 8 Pro
This repository contains basic code required to do ranging between the Qorvo DWM3001CDK and an Android phone (tested on Google Pixel 8 Pro). There is no Bluetooth implementation, out-of-band communication is done manually and the DWM3001CDK needs to be connected to a computer via USB to start ranging.

## Android app
The `android_app` directory contains a simple UWB project that is capable of starting and stopping a ranging session and displaying the resulting data.

## Python script
The `python_script` directory contains a copy of the script found in the [DWM3001CDK DK Software, Sources, Tools and Developer Guide.zip](https://www.qorvo.com/products/d/da008604) archive provided by Qorvo. It is modified slightly to work with Android. The modifications are listed below:
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