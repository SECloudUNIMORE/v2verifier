import struct
import math
import socket
from fastecdsa import ecdsa
from hashlib import sha256
from datetime import datetime

import v2verifier.V2VCertificates


def generate_v2v_bsm(latitude: float, longitude: float, elevation: float, speed: float, heading: float) -> bytes:
    """Create a BSM bytearray reporting vehicle position and motion data

    :param latitude: latitude of the vehicle position in degrees
    :type latitude: float
    :param longitude: longitude of the vehicle position in degrees
    :type longitude: float
    :param elevation: elevation of the vehicle in meters
    :type elevation: float
    :param speed: the speed of the vehicle in meters per second
    :type speed: float
    :param heading: the direction of travel measured in degrees
    :type heading: float

    :return: a BSM reporting vehicle position and motion
    :rtype: bytes
    """
    return struct.pack("!fffff", latitude, longitude, elevation, speed, heading)


def generate_1609_spdu(bsm: bytes, private_key: int) -> bytes:
    """Create a bytes object representing an IEEE 1609.2 SPDU

    :param bsm: a bytes object containing the BSM data for this message
    :type bsm: bytes
    :param private_key: an ECDSA private key to use for signing the SPDU
    :type private_key: int

    :return: a 1609.2-compliant SPDU
    :rtype: bytes
    """

    llc_dsap_ssap = 43690  # 0xaaaa -> SNAP extension
    llc_control = 3  # 0x03 -> connectionless mode (no ACKs)
    llc_type = 35036  # 0x88dc -> WSMP

    llc = struct.pack("!HbxxxH",
                      llc_dsap_ssap,
                      llc_control,
                      llc_type)

    wsmp_n_subtype_opt_version = 3  # 0x03 -> version 3
    wsmp_n_tpid = 0  # 0x00 -> no WSMP transport layer process specified
    wsmp_t_header_length_and_psid = 32  # 0x20 -> length 4 bytes, no PSID specified
    wsmp_t_length = 0  # 0x00 -> length of optional T-Header fields is zero

    wsm_headers = struct.pack("!bbbb",
                              wsmp_n_subtype_opt_version,
                              wsmp_n_tpid,
                              wsmp_t_header_length_and_psid,
                              wsmp_t_length)

    protocol_version = 3
    content_type = 129  # 0x81 -> signedData
    hash_id = 0  # 0x00 -> SHA-256
    section_offset = 64  # 0x40 -> offset new substructure
    section_start = 128  # 0x80 -> start substructure
    length_of_unsecured_data = len(bsm)  # length in bytes of BSM parameter

    ieee1609_dot2_data = struct.pack("!bBbbbBB",
                                     protocol_version,
                                     content_type,
                                     hash_id,
                                     section_offset,
                                     protocol_version,
                                     section_start,
                                     length_of_unsecured_data)

    ieee1609_dot2_data += bsm

    header_info = 1  # 0x01 -> start structure here
    header_psid = 32  # 0x20 -> Blind Spot Monitoring (generic V2V safety, no PSIDs are standardized yet)

    # The generationTime per 1609.2 is the number of elapsed microseconds since 00:00 Jan 1 2004 UTC
    generation_time = math.floor((datetime.now() - datetime(2004, 1, 1, 0, 0, 0, 0)).total_seconds() * 1000)

    # TODO: this might be a duplicate field with V2VCertificates.... fix if needed
    signer_identifier = 129  # 0x81 -> certificate

    ieee1609_dot2_data += struct.pack("!BBBQB",
                                      section_offset,
                                      header_info,
                                      header_psid,
                                      generation_time,
                                      signer_identifier,
                                      )

    ieee1609_dot2_data += v2verifier.V2VCertificates.get_implicit_certificate()

    signature_format = 128  # 0x80 -> x-only for signature value

    ieee1609_dot2_data += struct.pack("!BB",
                                      section_start,
                                      signature_format)

    r, s = ecdsa.sign(bsm, private_key, hashfunc=sha256)

    ieee1609_dot2_data += r.to_bytes(32, 'big') + s.to_bytes(32, 'big')

    return llc + wsm_headers + ieee1609_dot2_data


def send_v2v_message(msg: bytes, ip_address: str, port: int) -> None:
    """Send a V2V message using network communications

    :param msg: the message to send
    :type msg: bytes
    :param ip_address: the IP address to connect to and send the message
    :type ip_address: str
    :param port: the port to connect to and send the message
    :type port: int
    """

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(msg, (ip_address, port))