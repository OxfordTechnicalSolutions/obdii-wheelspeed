=====================
Getting Started Guide
=====================

How-to guide for connecting CAN wheelspeed from a vehicle to an OxTS navigation unit via the GAD interface

Disclaimer:
-----------
**WARNING:** Connecting directly to the vehicle's CAN bus via OBD-II could create unintended issues with the Engine Control Unit (ECU), which may cause error messages or even failure of the ECU itself. It is not advised to send data into the CAN bus, and even when used correctly it is possible that errors may occur. Operation only on private land is advised, unless some level of certainty of the vehicle's CAN bus is known (e.g. if you are the manufacturer of the vehicle).

Hardware used:
--------------
* CAN to USB converter (PEAK CANFD Pro)
   * Used to convert the CAN bus to a standard USB input for the PC, any CAN to USB (or other connection) could be used, bearing in mind driver requirements for the PC
* OBD-II to DB9 CAN cable (Kvaser)
   * Allows for the CAN pin out from the OBD-II port to go to the standard CAN bus DB9 connector
   * *IMPORTANT!* There are a number of OBD-II to DB9 converters on the market, but some have different pin-outs for the DB9 connector. For the PEAK unit, as well as many other CAN to USB converters, CAN high should be on pin 7 and CAN low on pin 2. Make sure you get the correct pinout for your CAN convertor.
   * One may be able to utilise an OBD-II to USB (or other bus) converter directly, however driver support will be important, as well as data accessibility on the PC.
* PC with USB and ethernet connections
   * USB used for CAN input via converter (another bus could be used with the right converter)
   * Ethernet used for GAD output to unit
   * Important to check driver support for CAN to USB device - this is normally fine for Windows, but Linux driver support can be less common. The PEAK unit was used here for the linux drivers so that a small unit such as a Raspberry Pi or Jetsen Nano could be used for the processing

Software used:
--------------
* Drivers for CAN to USB converter
* OXTS GAD-SDK and Python front-end (https://github.com/OxfordTechnicalSolutions/gad-sdk)
* Python 3 for scripting
* Python-CAN library (https://python-can.readthedocs.io/en/master/)
* Pip to install python libraries
* SavvyCAN (https://savvycan.com/) for checking of CAN output

=================
Preparatory work:
=================
The first thing that's needed is to understand what CAN message gives the wheelspeed from the car. If the ID and structure of the CAN message is already known, that will make things much easier. Otherwise, it may be possible to determine a signal which corresponds to wheelspeed by observing any CAN data.
The CAN to USB connection should be checked by utilising SavvyCAN. Please refer to the documentation of that project for more in-depth information, but for simply checking the CAN bus the following steps can be used:

1. Physically connect the CAN to USB device to the PC
2. Open SavvyCAN and open the 'connection' menu from the toolbar at the top
3. In the connection window, select 'Add New Device Connection' and select the appropriate connection and create the connection

    * In the case of this hardware, this is the 'QT SerialBus Devices' option, and then the device type should be 'PeakCan' and the relevant USB port.
4. Once you have created a connection, select it in the window and make sure the speed of the bus is correct

    * **NOTE:** If you have a bus speed that does not match the vehicle's CAN bus, it can easily cause ECU errors, especially if the rate is too high
5. It is also recommended to select 'listen only' in the connection options to prevent any accidental transmission onto the bus
6. With the connection set up, the main screen will automatically show any CAN messages seen on the bus
7. Connect the OBD-II to DB-9 connector first to the vehicle, then to the CAN to USB convertor
8. Turn the car's ignition on
9. CAN messages should begin appearing on the main SavvyCAN window - which can be checked as necessary

Once this physical connection has been made and checked, the connection can be closed in SavvyCAN in the connection menu, or by exiting SavvyCAN completely. With the hardware in place, the python code for creating the GAD packets can be used to send information to the OXTS unit.
For future connections, the SavvyCAN portion of this preparatory work can be bypassed, and the physical connection is all that needs setup.

=================================
Code and OXTS unit configuration:
=================================
Setting up the OXTS unit should be done in a usual fashion, making sure to have an ethernet connection to the unit via the PC which is receiving the CAN messages.
To configure the wheelspeed via GAD, the lever arm can be set in the wheelspeed tab of the 'advanced settings' in NAVConfig. Then, in the 'commands' section, the following config is needed::

    -gad_on[stream_id]
    -aid_wspeed_off
    -wheelspeed1000_10

The first command simply tells the unit to accept and use a GAD stream (with the ID that you assign in the code). The second turns off the in-built wheelspeed interface of the unit, so that GAD packets can be used for this instead. The final command sets the number of units per meter to be used by the wheelspeed calculation. 

The code required to convert the CAN message into a GAD packet is very minimal, once all of the external libraries are used in Python. The python-can library allows reading the CAN messages, and the oxts-sdk library enables creation and sending of the GAD packet.
The code first needs the IP of the unit to send the GAD packets too, as well the stream ID. The stream ID can be anything from 128 to 255, and should just not clash with any other GAD streams going to the unit (see the GAD SDK documentation for more details).
Then, the CAN bus can be set up, based on the type of the CAN to USB convertor, and the required bitrate. A handler for the GAD packets can also then be set up, pointing to the IP of the required unit.

The meat of the program can then be run. For each message coming in, we can check for the appropriate message ID, and then act upon it when found.
The Python-CAN library includes event listeners to check for specific messages, which are probably a better way to implement this, but the basic read through the bus worked for our on-site testing.
The message can then be read (8 bytes), and the required bytes can be converted to the speed. In this case, the speed in km per hour is represented by the final 2 bytes of the message, big-endian, unsigned, and with a scale factor of 1/100 (i.e. 0-655.36km/h).
Finally, we can convert this into meters per second, and then fill out a gad packet. The GAD packet needs a stream ID, then the speed (in this case 1000PPM is set by the -wheelspeed1000_10 command, so multiply by 1000) and variance (expects pulses squared, so for e.g. 0.2m error we use 0.2*1000 = 200, then square to get 40000).
The time can be given a timestamp, but in this case there is no good timing reference other than the OXTS unit. As such, setting either time_void (timestamp the packet as soon as the unit receives it) or passing a latency is the best route. See the 'improving output' section for more on this.
The lever arm needs to be set to optimising, and then the packet can be sent to the unit.

To check that the unit is receiving wheelspeed packets, the easiest way to check live is to remove the GNSS antennas and hold the unit stationary. If this is done without any other aiding sources, the velocity of the unit will start to drift, and the position will drift exponentially. If the wheelspeed packets are being received correctly, the velocity should remain very close to zero, and the position should only slowly drift.

=================
Improving Output:
=================
The basic script makes quite a few assumptions about the data that is gathered for wheelspeed, and the actual response of the system can be dramatically improved just by taking data with the system and analysing it to improve the configuration.
By taking a dataset out in an area with good GNSS coverage, post-processing can be done to obtain a dataset with just GNSS data that can be compared against wheelspeed, which can then be more trusted in areas with poor or no GNSS coverage.

By using another command, the full GAD data can be output by the system in order to analyse it later. This can be done using the command ``-gad_csv_output_resolved``, which will also include the timestamp when it was received by the system.
This can then be compared against the system data, for example by comparing it against a dataset processed with just GNSS data (ideally with RTK corrections), and comparing the NCOM output of forward velocity against the wheelspeed.
This can allow a comparison of the latency and variance of the wheelspeed, simply by looking at the two data signals and trusting the GNSS data to a suitable extent. The variances can then be changed as shown in the variance line of the code, and the latency can be changed using the ``time_latency`` command instead of ``time_void``.

The other item of configuration which can affect the quality of the output is the data rate. The data rate should actually NOT be as high as possible, and is in fact normally most effective when the data rate is between 5 and 50Hz. The best way to check this is to simply post-process the code with GNSS only, and compare against a GNSS-blanked period with the aiding at different rates.
To vary the data rate, one can use the 'stream priority' option (see the GAD-SDK documentation), but using the same stream ID in both places in the command. This means that the system will reject updates for a given time frame of that stream after receiving an update, thus changing the data rate.
Once all of the various configuration options are optimised, the system will perform its best.
