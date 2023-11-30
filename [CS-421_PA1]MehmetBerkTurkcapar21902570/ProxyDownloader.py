import socket
import sys
from datetime import datetime

def download_file(url, cache):
    # Parse the filename from the URL
    file_name = url.split("/")[-1]
    host_name = url.split("/")[2]
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host_name, 80))
    if file_name in cache:
        cache_last_modified = cache[file_name]
        print(f"Already downloaded '{file_name}' before...")
        print(f"Checking the Last-Modified information...")
        head_request = b"HEAD " + url.encode() + b" HTTP/1.1\r\nHost: " + host_name.encode() + b"\r\nConnection: close\r\n\r\n"
        s.sendall(head_request)
        response = b""
        while True:
            data = s.recv(1024)
            if not data:
                break
            response += data

        # Check the status code and status message
        response_lines = response.decode().split("\r\n")
        status_line = response_lines[0]
        status_code, status_message = int(status_line.split()[1]), " ".join(status_line.split()[2:])
        print(f"Retrieved: {status_code} {status_message} (for HEAD request)")

        # Check if response is OK and get the last modified time of the server file
        if status_code == 200:
            last_modified = response_lines[3].split(": ")[1].strip()
            last_modified = datetime.strptime(last_modified, "%a, %d %b %Y %H:%M:%S %Z")
            # Compare the last modified times of the cached file and server file
            if last_modified <= cache_last_modified:
                print("File is up-to-date in the cache, no need to send a new request...")
                print("Moving on...\n")
                s.close()
                return
            else:
                print("The file is not up-to-date in the cache, sending a new request...")
        else:
            print("ERROR: Couldn't check the server for Last-Modified\n")
            s.close()
            return
    # Send an HTTP GET request to download the file
    request_body = b"GET " + url.encode() + b" HTTP/1.1\r\nHost: " + host_name.encode() + b"\r\nConnection: close\r\n\r\n"
    s.sendall(request_body)
    response = b""
    while True:
        data = s.recv(1024)
        if not data:
            break
        response += data
    # Check the status code and status message
    response_lines = response.decode().split("\r\n")
    status_line = response_lines[0]
    status_code, status_message = int(status_line.split()[1]), " ".join(status_line.split()[2:])
    print(f"Retrieved: {status_code} {status_message} (for GET request)")

    # Check if response is OK
    if status_code != 200:
        print("ERROR: File not found, moving on...\n")
        return
    last_modified = response_lines[3].split(": ")[1].strip()
    cache[file_name] = datetime.strptime(last_modified, "%a, %d %b %Y %H:%M:%S %Z")
    # Save the file
    f = open(file_name, "wb")
    f.write(response.split(b"\r\n\r\n")[1])
    print(f"Downloading file '{file_name}'...")
    print("Saving file...\n")
    s.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python ProxyDownloader.py <port>")
        sys.exit(1)
    proxy_port = sys.argv[1]
    # Initialize the cache as empty dictionary
    cache = {}
    # Create a socket and listen on the designated port
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("", int(proxy_port)))
    s.listen()
    print(f"Listening on port {proxy_port}...")

    # Infinite loop to accept incoming connections
    while True:
        print("----------------------------------------")
        print("Waiting for a connection...")
        conn, addr = s.accept()
        # Read the HTTP request
        request = b""
        while True:
            data = conn.recv(1024)
            request += data
            if b"\r\n\r\n" in request:
                break
        # Parse the URL from the HTTP request
        url = request.split(b"\r\n")[0].split(b" ")[1].decode()
        host_name = url.split("/")[2]
        print(f"Retrieved request from Firefox:")
        if host_name != 'www.cs.bilkent.edu.tr':
            print('WARNING: Host name is not www.cs.bilkent.edu.tr, moving on...\n')
            continue
        print(request.decode())
        # Download the file
        download_file(url, cache)
