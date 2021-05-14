import struct


def generate_v2v_bsm(latitude: float, longitude:float, elevation: float, speed: float, heading: float) -> bytes:
    """Create a BSM bytearray reporting vehicle position and motion data

    Parameters:
        latitude (float): latitude of the vehicle position in degrees
        longitude (float): longitude of the vehicle position in degrees
        elevation (float): elevation of the vehicle in meters
        speed (float): the speed of the vehicle in meters per second
        heading (float) the direction of travel measured in degrees (relative to what?)

    Returns:
        bytes

    """

    return struct.pack("fffff", latitude, longitude, elevation, speed, heading)


def generate_1609_spdu(bsm: bytes) -> bytes:
    """Create a bytes object representing an IEEE 1609.2 SPDU

    Parameters:
        bsm (bytes): a bytes object containing the BSM data for this message

    Returns:
        bytes
    """

    llc_dsap_ssap = 43690  # 0xaaaa -> SNAP extension
    llc_control = 3  # 0x03 -> connectionless mode (no ACKs)
    llc_type = 35036  # 0x88dc -> WSMP

    llc = struct.pack(">HbxxxH",
                      llc_dsap_ssap,
                      llc_control,
                      llc_type)

    wsmp_n_subtype_opt_version = 3  # 0x03 -> version 3
    wsmp_n_tpid = 0  # 0x00 -> no WSMP transport layer process specified
    wsmp_t_header_length_and_psid = 32  # 0x20 -> length 4 bytes, no PSID specified
    wsmp_t_length = 0  # 0x00 -> length of optional T-Header fields is zero

    wsm_headers = struct.pack(">bbbb",
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

    ieee1609Dot2Data = struct.pack(">bBbbbBB",
                                   protocol_version,
                                   content_type,
                                   hash_id,
                                   section_offset,
                                   protocol_version,
                                   section_start,
                                   length_of_unsecured_data)

    ieee1609Dot2Data += bsm

    header_info = 1  # 0x01 -> start structure here
    psid = 32  # 0x20 -> Blind Spot Monitoring (generic V2V safety, no PSIDs are standardized yet)
    generation_time = 0  # TODO: add a function to calculate time since Jan. 1 2004 per 1609.2

    ieee1609Dot2Data += struct.pack(">BBBQ",
                                    section_offset,
                                    header_info,
                                    psid,
                                    generation_time
                                    )

    print(llc + wsm_headers + ieee1609Dot2Data)



if __name__=="__main__":
    generate_1609_spdu(generate_v2v_bsm(43, -71, 1543, 45.36, 145.223))
