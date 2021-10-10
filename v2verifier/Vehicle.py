import time
import socket
import v2verifier.V2VReceive
import v2verifier.V2VTransmit
from fastecdsa import point


class Vehicle:
    """A class to represent a vehicle.

    :param public_key: the vehicle's public key
    :type public_key: fastecdsa.point.Point
    :param private_key: the vehicle's private key
    :type private_key: int
    """

    def __init__(self, public_key: point.Point, private_key: int) -> None:
        """Constructor for the vehicle class

        :param public_key: the vehicle's public key
        :type public_key: fastecdsa.point.Point
        :param private_key: the vehicle's private key
        :type private_key: int
        """

        self.public_key = public_key
        self.private_key = private_key
        self.bsm_interval = 0.1  # interval specified in seconds, 0.1 -> every 100ms
        self.known_vehicles = {}

    def run(self, mode: str, tech: str, pvm_list: list, test_mode: bool = False) -> None:
        """Launch the vehicle

        :param mode: selection of "transmitter" or "receiver"
        :type mode: str
        :param tech: choice of DSRC or C-V2X as V2V communication technology
        :type tech: str
        :param pvm_list: a list of vehicle position/motion data elements
        :type pvm_list: list
        :param test_mode: indicate whether test mode (w/o USRPs and GNURadio) should be used. Affects ports used.
        :type test_mode: bool, optional
        """

        if mode == "transmitter":
            for pvm_element in pvm_list:
                latitude, longitude, elevation, speed, heading = pvm_element.split(",")
                bsm = v2verifier.V2VTransmit.generate_v2v_bsm(float(latitude),
                                                              float(longitude),
                                                              float(elevation),
                                                              float(speed),
                                                              float(heading))

                spdu = v2verifier.V2VTransmit.generate_1609_spdu(bsm, self.private_key)

                if test_mode:  # in test mode, send directly to receiver on port 4444
                    v2verifier.V2VTransmit.send_v2v_message(spdu, "localhost", 4444)
                else:  # otherwise, send to wifi_tx.grc listener on port 52001 to become 802.11 payload
                    v2verifier.V2VTransmit.send_v2v_message(spdu, "localhost", 52001)

                time.sleep(self.bsm_interval)

        elif mode == "receiver":
            if tech == "dsrc":
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.bind(("127.0.0.1", 4444))
                while True:
                    data = sock.recv(2048)

                    if test_mode:  # in test mode, there are no 802.11 headers, so parse all received data
                        spdu_data = v2verifier.V2VReceive.parse_received_spdu(data)
                    else:  # otherwise (i.e., w/ GNURadio), 802.11 PHY/MAC headers must be stripped before parsing SPDU
                        spdu_data = v2verifier.V2VReceive.parse_received_spdu(data[57:])

                    verification_data = v2verifier.V2VReceive.verify_spdu(spdu_data, self.public_key)
                    bsm_data_tuple = v2verifier.V2VReceive.extract_bsm_data(spdu_data["tbs_data"]["unsecured_data"], verification_data)
                    self.update_known_vehicles(spdu_data["certificate"]["hostname"], bsm_data_tuple, verification_data)

                    print(v2verifier.V2VReceive.get_bsm_report(spdu_data["tbs_data"]["unsecured_data"], verification_data))
                    v2verifier.V2VReceive.report_bsm_gui(bsm_data_tuple, verification_data, "127.0.0.1", 6666)

            elif tech == "cv2x":
                # use IPv6 on the Ethernet interface to get messages from COTS device
                sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
                sock.bind(("fe80::ca89:f53:4108:d142%enp3s0", 4444, 0, 2))
                while True:
                    data = sock.recv(2048)
                    bsm_data = v2verifier.V2VReceive.parse_received_cv2x_spdu(data)

                    # v2verifier.V2VReceive.parse_received_cv2x_spdu() returns empty dict if
                    # the SPDU is below a certain length threshold. This prevents attempting
                    # to parse non-BSMs, e.g., control messages, as if they were BSMs
                    if bsm_data == {}:
                        continue

                    print(v2verifier.V2VReceive.report_cots_cv2x_bsm(bsm_data))
            else:
                raise Exception("Technology must be specified as \"dsrc\" or \"cv2x\".")

        else:
            raise Exception("Error - Vehicle.run() requires that mode be specified as either "
                            "\"transmitter\" or \"receiver\".\nCheck your inputs and try again.")

    def update_known_vehicles(self, id: str, bsm_data: tuple, verification_data: dict) -> None:
        """Update the vehicle's threat tracking \"database\"

        :param id: the vehicle identifier from the BSM
        :type id: str
        :param bsm_data: BSM data from an SPDU
        :type bsm_data: tuple
        :param verification_data: security information from verify_spdu()
        :type verification_data: dict
        """
        if id not in self.known_vehicles.keys():
            self.known_vehicles[id] = {}

        self.known_vehicles[id]["latitude"] = bsm_data[0]
        self.known_vehicles[id]["longitude"] = bsm_data[1]
        self.known_vehicles[id]["elevation"] = bsm_data[2]
        self.known_vehicles[id]["speed"] = bsm_data[3]
        self.known_vehicles[id]["heading"] = bsm_data[4]

        self.known_vehicles[id]["signature_type"] = verification_data["signature_type"]
        self.known_vehicles[id]["valid_signature"] = verification_data["valid_signature"]
        self.known_vehicles[id]["unexpired"] = verification_data["unexpired"]
        self.known_vehicles[id]["elapsed"] = verification_data["elapsed"]

    def report_known_vehicles(self):
        """Print out report of all known vehicles and all data elements for each known vehicle
        """
        for vehicle in self.known_vehicles.keys():
            print("Vehicle: ", vehicle)
            for item in self.known_vehicles[vehicle]:
                print("\t", item, self.known_vehicles[vehicle][item])