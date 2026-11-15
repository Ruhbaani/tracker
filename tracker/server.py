import hashlib
import socket
import struct
import sys
from pathlib import Path


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
    host = "127.0.0.1"
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    files_folder = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("files")

    filehashes = {}

    # Calculate SHA-256 hashes for available file parts.
    for file_path in files_folder.iterdir():
        if file_path.is_file():
            hasher = hashlib.sha256()

            with file_path.open("rb") as file:
                while True:
                    chunk = file.read(65536)

                    if not chunk:
                        break

                    hasher.update(chunk)

            file_hash = hasher.hexdigest()
            filehashes[file_hash] = file_path

            print(f"{file_path.name}: {file_hash}")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port))
        s.listen(5)

        print(f"File server listening on port {port}")

        while True:
            conn, addr = s.accept()

            with conn:
                try:
                    requested_hash = receive_line(conn)
                    print(f"Received hash: {requested_hash}")

                    file_path = filehashes.get(requested_hash)

                    if file_path is None:
                        conn.sendall(b"nofile\n")
                        reply = receive_line(conn)
                        print(f"Client reply: {reply}")
                        continue

                    with file_path.open("rb") as file:
                        file.seek(0, 2)
                        file_size = file.tell()
                        file.seek(0)

                        conn.sendall(b"gotfile\n")

                        reply = receive_line(conn)

                        if reply != "ackfile":
                            raise ConnectionError(
                                "Expected ackfile from client."
                            )

                        conn.sendall(
                            struct.pack("!Q", file_size)
                        )

                        remaining = file_size

                        while remaining > 0:
                            chunk = file.read(min(65536, remaining))

                            if not chunk:
                                raise OSError(
                                    "File ended before expected size."
                                )

                            conn.sendall(chunk)
                            remaining -= len(chunk)

                        print(
                            f"Sent {file_path.name}: {file_size} bytes"
                        )

                except (OSError, ConnectionError) as error:
                    print(f"Transfer failed: {error}")


if __name__ == "__main__":
    main()