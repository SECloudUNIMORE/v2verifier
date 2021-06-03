def read_data_from_file(filepath: str) -> list:
    """Reads in vehicle motion data from a CSV text file

    :param filepath: the filepath to a CSV text file of vehicle motion data.
    :type filepath: str

    :return: a list of position/motion strings formatted as "latitude,longitude,elevation,speed,heading"
    :rtype: list
    """

    try:
        with open(filepath, "r") as infile:
            # TODO: add a check here to validate the input. For now, we'll assume the user knows what they're doing
            data = infile.readlines()
            return data

    except FileNotFoundError:
        print("Error - could not open the file at ", filepath)
        print("Fatal error. Exiting.")
        exit(1)
