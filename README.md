# V2Verifier

****Important** - this version of V2Verifier (v3.0.0) is a _preliminary release._ 
As we await bug fixes in third-party open-source projects that V2Verifier relies on
for C-V2X sidelink communication, **this version of V2Verifier temporarily does 
not support C-V2X**. We thank you for your patience as we work towards resolving this
issue.**

V2Verifer is an open-source testbed for experimental evaluation of security in
vehicle-to-vehicle (V2V) communication. V2Verifier supports a broad range of 
experimentation with V2V technologies and security protocols using a 
combination of software-defined radios (e.g., USRPs) and commercial V2V
equipment. Among other features, V2Verifier includes implementations of:
- Security features from the IEEE 1609.2 standard for V2V security, including
message signing and verification and V2V certificates
- WAVE Short Message Protocol (IEEE 1609.3)
- Dedicated Short Range Communication (DSRC) - adapted from 
the [WiME Project's](http://dx.doi.org/10.1109/TMC.2017.2751474)
IEEE 802.11p transceiver
- ~~Cellular Vehicle-to-Everything (C-V2X) - based on the 
[srsRAN](https://github.com/srsRAN/srsRAN) project (formerly
srsLTE)~~ (temporarily not supported)

Check out our 
[YouTube page](https://www.youtube.com/channel/UC5lY5D4KYgfKu3FXtfjHP7A)
for some of our past projects and publications that made use of V2Verifier!

V2Verifier is developed and maintained in the [Wireless and IoT Security 
and Privacy (WISP)](https://www.rit.edu/wisplab/) lab at Rochester Institute
of Technology's [Global Cybersecurity Institute](
https://rit.edu/cybersecurity).

### Citing V2Verifier
If you use V2Verifier or any of its components in your work, please cite 
[our paper](https://github.com/twardokus/v2verifier/wiki/Publications) from 
IEEE ICC 2021. Additional publications involving V2Verifier are listed on the 
same page.

## Requirements
V2Verifier is designed for over-the-air experiments with software-defined radios 
(SDRs).
For C-V2X, you _**must**_ use SDRs with GPSDO modules installed. We recommend
the USRP B210 and TCXO GPSDO module from Ettus Research (we have not tested and 
do not officially support the use of other SDRs for C-V2X).
For DSRC, you may use USRP B210s (GPSDO not required for DSRC) or, preferably, 
USRP N210s (also available from Ettus Research). If you are using N210s, a 6 GHz 
daughterboard (e.g., UBX 40) is required for each N210 device.

If you do not have access to SDRs, V2Verifier can also be run as a pure 
simulation environment that only requires a modern PC to run. With or without
SDRs, we strongly discourage the use of virtual machines as this may incur 
testbed-breaking latency. Ubuntu 20.04 is currently the only supported
operating system. **Windows operating systems are not supported.**

## Installing V2Verifier

To install V2Verifier, follow the general instructions below, as well as the specific
instructions for the V2V technology you want to experiment with, for _each_ PC
that you will use to run experiments.

### C-V2X

**C-V2X support has been temporarily removed as we await bug fixes in third-party code
that V2Verifier relies on. Thank you for your patience as we work to restore this
functionality as soon as possible.**

### DSRC

[GNURadio](https://github.com/gnuradio/gnuradio) version 3.8 is required to run
DSRC experiments in V2Verifier. Additionally, GNURadio modules from the 
[WiME project](https://www.wime-project.net/)] are required. Install GNURadio
as well as the required WiME modules with the following commands. If you
encounter any errors, please visit the GNURadio project for their most recent
installation instructions and troubleshooting guide.

    sudo apt install -y python3-pip
    sudo -H pip3 install PyBOMBS
    pybombs auto-config
    pybombs recipes add-defaults
    mkdir ~/gr38
    pybombs prefix init ~/gr38 -R gnuradio-default
   
    pybombs install gr-foo
    pybombs install gr-ieee-80211

To ensure installation was successful, execute the following command to 
run GNURadio Companion.

    pybombs run gnuradio-companion

Next, on each Ubuntu PC, you must install the following dependencies:

	sudo apt install -y git cmake libuhd-dev uhd-host swig libgmp3-dev python3-pip python3-tk python3-pil 
	python3-pil.imagetk 

If you have not already cloned the repository, do so with the commands

    cd ~
    git clone https://github.com/twardokus/v2verifier.git

Move into the V2Verifier directory and build the project using the standard CMake
build process:

    cd v2verifier
    mkdir build
    cd build
    cmake ../
    make

Once the project is built, proceed to the next section for instructions on how to
run experiments in V2Verifier.

## Running V2Verifier

Begin by connecting one USRP to each PC.

### Radio layer: C-V2X
*Note C-V2X communication requires equipment capable of both cellular
communication and GPS clock synchronization (e.g., USRP B210 w/ GPSDO or
[Cohda Wireless MK6c](https://cohdawireless.com/solutions/hardware/mk6c-evk/)) as well as access to either an outdoor
testing environment or synthesized GPS source.*

**C-V2X support has been temporarily removed as we await bug fixes in third-party code
that V2Verifier relies on. Thank you for your patience as we work to restore this
functionality as soon as possible.**


### Radio layer: DSRC

On both PCs, launch GNURadio with the command `gnuradio-companion` from a terminal. 
On one PC, open the `wifi_tx.grc` file from the `v2verifier/grc` project subdirectory. On the other PC, open 
the `wifi_rx.grc` file from the same subdirectory. Click the green play button at the top of GNURadio to launch the 
flowgraphs on both PCs. You will need to configure the communication options (e.g., bandwith, frequency) to suit your 
needs. The default is a 10 MHz channel on 5.89 GHz.

On each PC, `cd` into the `build` directory. For the receiver, run the command

    ./src/v2verifier dsrc receiver [--test] [--gui]

For the transmitter, run the command

    ./src/v2verifier dsrc transmitter [--test]
    
See the command-line help (`./v2verifier -h`) for optional arguments.



## Important note about GUIs
V2Verifier currently offers two graphical 
interfaces. The first is a web-based interface that interacts with Google Maps. 
To use this GUI, you will need to purchase a Google Maps API key through Google 
Cloud services and create `config.js` file in the `web` directory of V2Verifier
(some familiarity with JavaScript is helpful). 

Our second interface is based on
TkGUI. To use this option, open a separate terminal window before running any 
`v2verifier` commands above and run `python3 tkgui_execute.py` to launch the 
TkGUI interface as a separate process. We encourage you to open a GitHub issue
with any questions or problems using either graphical interface.