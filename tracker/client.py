import hashlib
import socket
import struct
import json
from pathlib import Path


TRACKER_HOST = "127.0.0.1"
TRACKER_PORT = 6000


def receive_line(s):
    data = bytearray()

    while True:
        byte = s.recv(1)

        if not byte:
            raise ConnectionError("Disconnected during message.")

        if byte == b"\n":
            return data.decode("utf-8")

        data.extend(byte)


def receive_exactly(s, size):
    data = bytearray()

    while len(data) < size:
        chunk = s.recv(min(65536, size - len(data)))

        if not chunk:
            raise ConnectionError(
                "Server disconnected before transfer finished."
            )

        data.extend(chunk)

    return data


def get_server_location(requested_hash):
    """Ask tracker which server contains the requested part."""

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((TRACKER_HOST, TRACKER_PORT))

        s.sendall((requested_hash + "\n").encode("utf-8"))

        response = receive_line(s)

        if response == "nofile":
            return None

        location = json.loads(response)

        print(f"Tracker returned: {location}")

        return location


def download_part(host, port, requested_hash):
    """Download and verify one file part."""

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))

        s.sendall((requested_hash + "\n").encode("utf-8"))

        response = receive_line(s)

        if response == "nofile":
            s.sendall(b"acknone\n")
            return None

        if response != "gotfile":
            raise ConnectionError(
                f"Unexpected server response: {response}"
            )

        s.sendall(b"ackfile\n")

        size_bytes = receive_exactly(s, 8)
        file_size = struct.unpack("!Q", size_bytes)[0]

        part_data = receive_exactly(s, file_size)

        actual_hash = hashlib.sha256(part_data).hexdigest()

        if actual_hash != requested_hash:
            raise ValueError(
                "Downloaded part does not match requested hash."
            )

        print(f"Downloaded {file_size} bytes from {host}:{port}")

        return part_data


def main():
    part1 = "b13732c67903031abcd006a4c02bc4fe778692d2d640758cea93846997b2a367"
    part2 = "9d64b30c3d2047a1c0c77733134491c8a2dddc9354997038244ea9bd41bfc42f"

    finaldata = bytearray()

    try:
        for part_hash in [part1, part2]:

            # Step 1: Locate the part using the tracker.
            location = get_server_location(part_hash)

            if location is None:
                print(f"Tracker could not locate part: {part_hash}")
                return

            host = location["host"]
            port = location["port"]

            # Step 2: Connect directly to the server.
            part_data = download_part(host, port, part_hash)

            if part_data is None:
                print(f"Server does not have part: {part_hash}")
                return

            # Step 3: Append parts in the correct order.
            finaldata.extend(part_data)

        # Step 4: Save the complete file.
        output_path = Path("reassembled.bin")

        with output_path.open("wb") as file:
            file.write(finaldata)

        print(f"Saved {len(finaldata)} bytes to {output_path}")

    except (OSError, ConnectionError, ValueError, KeyError) as error:
        print(f"Download failed: {error}")


if __name__ == "__main__":
    main()