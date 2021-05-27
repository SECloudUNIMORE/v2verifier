import eel
import threading
import socket
import logging
import struct


class WebGUI:
    """A class to represent the Web-based V2Verifier GUI

    :param enable_logging: choice of whether to enable console logging for GUI, defaults to False
    :type enable_logging: bool
    """

    def __init__(self, enable_logging: bool = False):
        """WebGUI constructor
        """

        self.logging_enabled = True if enable_logging else False

        if self.logging_enabled:
            self.logger = logging.getLogger(__name__)
            self.logger.setLevel(logging.INFO)
            ch = logging.StreamHandler()
            ch.setLevel(logging.INFO)
            self.logger.addHandler(ch)

        self.receive_socket = None
        self.thread_lock = threading.Lock()

        #
        # with open("../init.yml", "r") as conf_file:
        #     self.config = yaml.load(conf_file, Loader=yaml.FullLoader)
        #
        # self.num_vehicles = self.config["remoteConfig"]["numberOfVehicles"] + 1
        # self.totalPackets = self.config["remoteConfig"]["traceLength"] * (
        #     self.num_vehicles - 1
        # )

        self.received_packets = 0
        self.processed_packets = 0
        self.authenticated_packets = 0
        self.intact_packets = 0
        self.on_time_packets = 0

        if self.logging_enabled:
            self.logger.info("Initialized GUI")

    def update_vehicle(self, vehicle_id: int, latitude: float, longitude: float, icon_path: str) -> None:
        """Update the GUI marker for a given vehicle

        :param vehicle_id: the ID number of the vehicle whose marker is being updated
        :type vehicle_id: int
        :param latitude: the new latitude where the marker should be placed
        :type latitude: float
        :param longitude: the new longitude where the marker should be placed
        :type longitude: float
        :param icon_path: the file path to an image to use as the marker on the map
        :type icon_path: str
        """
        if self.logging_enabled:
            self.logger.info(f"moving vehicle {vehicle_id} to {latitude}, {longitude}")

        # EEL exposes this function in main.html
        eel.updateMarker(vehicle_id, latitude, longitude, icon_path)

    def add_message(self, message):
        eel.addMessage(message)

    def prep(self):
        eel.init("web")

    def run(self):

        if self.logging_enabled:
            self.logger.info("called run, starting server")
            self.logger.info("starting for real")

        eel.start(
            "main.html"
        )

    def start_receiver(self):

        if self.logging_enabled:
            self.logger.info("called start_receiver, creating socket")

        self.receive_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.receive_socket.bind(("127.0.0.1", 6666))

        label_thread = threading.Thread(target=self.update_stats_labels)
        label_thread.start()

        self.receiver = threading.Thread(target=self.receive)
        self.receiver.start()

    def update_stats_labels(self):

        if self.logging_enabled:
            self.logger.info("starting update_stats_labels")

        while True:

            if self.received_packets == 0:
                continue

            eel.updatePacketCounts(
                self.received_packets,
                self.processed_packets,
                self.authenticated_packets,
                self.intact_packets,
                self.on_time_packets,
            )

            eel.sleep(0.1)

    def receive(self):
        if self.logging_enabled:
            self.logger.info("starting receive")

        while True:
            msg = self.receive_socket.recv(2048)
            data = struct.unpack("!5f??f", msg)

            if self.logging_enabled:
                self.logger.info("received data")

            self.received_packets += 1

            if data[5]:
                self.authenticated_packets += 1
                self.intact_packets += 1

            if data[6]:
                self.on_time_packets += 1

            update = threading.Thread(
                target=self.process_new_packet,
                args=(
                    0,  # data["id"],
                    data[0],  # data["x"],
                    data[1],  # data["y"],
                    data[2],
                    "N",  # TODO: fix this
                    # data[4],  # ["heading"],
                    data[5],  # data["sig"],
                    data[6],  # data["recent"],
                    False,  # data["receiver"],
                    data[7],  # data["elapsed"],
                ),
            )
            update.start()

    def process_new_packet(self, vehicle_id: int, latitude: float, longitude: float, elevation: float,
                           heading: float, is_valid: bool, is_recent: bool, is_receiver: bool,
                           elapsed_time: float) -> None:
        """Method to present data from a BSM on the GUI

        Parameters:
            vehicle_id (int): the ID number of the vehicle which sent the message
            latitude (float): the reported latitude
            longitude (float): the reported longitude
            elevation (float): the reported elevation
            heading (float): the reported heading (direction of travel)
            is_valid (bool): result of message verification
            is_recent (bool): result of message timestamp verification
            is_receiver (bool): True if the sender of the message is the receiver (for representing local vehicle)
            elapsed_time (float): the time elapsed between the BSM's generation time and the time this method is called

        Returns:
            None
        """

        if self.logging_enabled:
            self.logger.info(f"processing packet from {vehicle_id}")

        icon = ""
        if is_receiver:
            icon = f"/images/receiver/{heading}.png"
        elif is_valid:
            icon = f"/images/regular/{heading}.png"
        else:
            icon = f"/images/phantom/{heading}.png"

        self.update_vehicle(vehicle_id, latitude, longitude, icon)

        # print messages to gui

        # acquire lock

        message = f"<p>Message from {vehicle_id}:</p>"
        if not is_receiver:
            if is_valid:
                message += '<p class="tab">✔️ Message successfully authenticated</p>'
            else:
                message += '<p class="tab">❌ Invalid signature!\n</p>'

            if is_recent:
                rounded_time = 0
                if elapsed_time > 0:
                    rounded_time = str(round(elapsed_time, 2))

                message += f'<p class="tab">✔️ Message is recent: {rounded_time} ms since transmission<p>'

            else:
                rounded_time = str(round(elapsed_time, 2))
                message += '<p class="tab">❌ Message is out-of-date: {rounded_time} ms since transmission<p>'

            if not is_valid and not is_recent:
                message += '<p class="tab">❌❌❌ Invalid signature and message expired, replay attack likely ❌❌❌</p>'

            message += f'<p class="tab">Vehicle reports location at {latitude}, {longitude} traveling {heading}<p>'
            self.add_message(message)

            self.processed_packets += 1
