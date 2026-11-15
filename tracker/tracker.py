import socket
import json

HOST = "127.0.0.1"
PORT = 6000

# Mapping file-part hashes to server locations.
file_locations = {
    "b13732c67903031abcd006a4c02bc4fe778692d2d640758cea93846997b2a367": {
        "host": "127.0.0.1",
        "port": 5000
    },
    "9d64b30c3d2047a1c0c77733134491c8a2dddc9354997038244ea9bd41bfc42f": {
        "host": "127.0.0.1",
        "port": 5001
    }
}


def receive_line(conn):
    data = bytearray()

    while True:
        byte = conn.recv(1)

        if not byte:
            raise ConnectionError("Client disconnected.")

        if byte == b"\n":
            return data.decode("utf-8")

        data.extend(byte)


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen(5)

        print(f"Tracker listening on port {PORT}")

        while True:
            conn, addr = s.accept()

            with conn:
                try:
                    requested_hash = receive_line(conn)
                    print(f"Tracker received hash: {requested_hash}")

                    location = file_locations.get(requested_hash)

                    if location is None:
                        conn.sendall(b"nofile\n")
                    else:
                        response = json.dumps(location) + "\n"
                        conn.sendall(response.encode("utf-8"))

                        print(f"Sent location: {location}")

                except (OSError, ConnectionError) as error:
                    print(f"Tracker request failed: {error}")


if __name__ == "__main__":
    main()