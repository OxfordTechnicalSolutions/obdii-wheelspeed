#!\usr\bin\python

import oxts_sdk # Used to create and transmit GAD packets
import can # Used to request, receive and decode CAN packets
import time

unit_ip = "192.168.25.11"
stream_id = 130 # Must be between 128 and 255

# Set up the bus to receive CAN messages
bus = can.interface.Bus(bustype='pcan', channel='PCAN_USBBUS1', bitrate=1000000)

# Set up the handler to create and send GAD packets
gad_hand = oxts_sdk.GadHandler()
gad_hand.set_encoder_to_bin()
gad_hand.set_output_mode_to_udp(unit_ip)

#for msg in bus:
#   if msg.arbitration_id == 1541: # Acceleration message (3D)
#print(msg.data)
#print(msg.data[4:6])
#print("Acceleration: ", 0.01*float(int.from_bytes(msg.data[4:6], "little", signed="True")))
   # Z is 3rd set of 2 bytes, little endian, signed
#acc_z = 0.01*int.from_bytes(msg.data[4:6], "little", signed=True) 

print("Running GAD packets")
for msg in bus:
   if msg.arbitration_id == 1540: # Vehicle frame horizontal velocity
   # Forward is 1st set of 2 bytes, little endian, signed
      vf = 0.01*int.from_bytes(msg.data[0:2], "little", signed=True) 
#      print(vf)
      gad_speed = oxts_sdk.GadSpeed(stream_id)
#gad_speed.speed_fw = int(1000*vf)
      gad_speed.speed_fw = 0.0
#gad_speed.speed_fw_var = int(50*vf)
      gad_speed.speed_fw_var = 0.0001
#gad_speed.time_latency = 0.1 # Just an estimate, could measure for better results
      gad_speed.set_time_void()
      gad_speed.set_aiding_lever_arm_optimising()

      gad_hand.send_packet(gad_speed)
      print("Sent GAD packet")
      time.sleep(0.09)
