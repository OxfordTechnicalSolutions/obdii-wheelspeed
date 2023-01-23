#!\usr\bin\python

# To be reviewed by BK

import oxts_sdk # Used to create and transmit GAD packets
import can # Used to request, receive and decode CAN packets
import time

unit_ip = "192.168.25.11"
stream_id = 130 # Must be between 128 and 255
kmh_to_ms = 1.0 / 3.6

# Set up the bus to receive CAN messages
# Standard CAN output is at 500KHz
bus = can.interface.Bus(bustype='pcan', channel='PCAN_USBBUS1', bitrate=500000)

# Set up the handler to create and send GAD packets
gad_hand = oxts_sdk.GadHandler()
gad_hand.set_encoder_to_bin()
gad_hand.set_output_mode_to_udp(unit_ip)

# Appears to come from Ford's CAN messages
for msg in bus:
   if msg.arbitration_id == 0x130:
      # Vehicle speed is 7th and 8th return byte, big endian, unsigned
      speed_kmh = 0.01*int.from_bytes(msg.data[6:8], "big", signed=False) 
      speed_ms = speed_kmh*kmh_to_ms
      gad_speed = oxts_sdk.GadSpeed(stream_id)
      gad_speed.speed_fw = int(1000*speed_ms) # Wheelspeed uses 1000 pulses per meter
#gad_speed.speed_fw_var = (int(50*speed_ms+10))^2 # Variance 5%
      gad_speed.speed_fw_var = 40000 # Variance 5%
      gad_speed.set_time_void()
#gad_speed.time_latency = 0.1 # Just an estimate, could measure for better results
      gad_speed.set_aiding_lever_arm_optimising()

      gad_hand.send_packet(gad_speed)
      print("Sent GAD packet. Wheelspeed {}m/s.".format(speed_ms))
