#!/usr/bin/env python3
# Copyright (c) 2021 Qorvo US, Inc.

import argparse
import logging
import time

from uci.v1_0 import App, Client

parser = argparse.ArgumentParser(description='Fira app equivalent using UCI.')
parser.add_argument('-p', '--port', type=str,
                    help='port use for serial', default='/dev/ttyACM0')
parser.add_argument('--controlee', action='store_true',
                    help='start in controlee mode (default controller mode)',
                    default=False)
parser.add_argument('-d', '--duration', type=int,
                    help='duration of the ranging session', default=10)
parser.add_argument('-v', '--verbose', action='store_true',
                    help='use logging.DEBUG level',
                    default=False)
parser.add_argument('-c', '--channel', type=int,
                    help='channel number', default=9)
parser.add_argument('-s', '--session_id', type=int,
                    help='session id', default=42)
parser.add_argument('-a', '--address', type=str,
                    help='device address', default='00:00')
parser.add_argument('-t', '--target', type=str,
                    help='target address', default='01:00')

args = parser.parse_args()

if args.verbose:
    logging.basicConfig(level=logging.DEBUG)

# Parse the address and target, bytes are reversed
dev_mac = int(args.address[-2:] + args.address[0:2], 16)
dst_mac = int(args.target[-2:] + args.target[0:2], 16)

client = Client(port=args.port)

print('init:',
      client.session_init(args.session_id, 0))

if not args.controlee:
    print('set app:',
          client.session_set_app_config(args.session_id, [
              (App.DeviceType, 1),
              (App.DeviceRole, 1),
              (App.DeviceMacAddress, dev_mac),
              (App.NumberOfControlees, 1),
              (App.DstMacAddress, [dst_mac]),
          ]))
else:
    print('set app:',
          client.session_set_app_config(args.session_id, [
              (App.DeviceType, 0),
              (App.DeviceRole, 0),
              (App.DeviceMacAddress, dev_mac),
              (App.DstMacAddress, [dst_mac]),
          ]))

print('set app:',
      client.session_set_app_config(args.session_id, [
          (App.ResultReportConfig, 0xb),
          (App.VendorId, 0x0708),
          (App.StaticStsIv, 0x060504030201),
          (App.AoaResultReq, 1),
          (App.UwbInitiationTime, 1000),
          (App.RangingRoundUsage, 2),
          (App.ChannelNumber, args.channel),
          (App.PreambleCodeIndex, 9)
      ]))

print('set app:',
      client.session_set_app_config(args.session_id, [
          (App.RframeConfig, 3),
          (App.SfdId, 2),
          (App.SlotDuration, 2400),
          (App.RangingInterval, 120),
          (App.SlotsPerRr, 6),
          (App.MultiNodeMode, 0),
          (App.HoppingMode, 1),
          (App.RssiReporting, 1),
          (App.EnableDiagnostics, 1),
          (App.DiagsFrameReportsFields, 1)
      ]))

print('config:',
      client.session_get_app_config(args.session_id, []))

print('start:',
      client.session_start(args.session_id))

time.sleep(args.duration)

print('stop:',
      client.session_stop(args.session_id))

time.sleep(2)

print('deinit:',
      client.session_deinit(args.session_id))

time.sleep(2)
