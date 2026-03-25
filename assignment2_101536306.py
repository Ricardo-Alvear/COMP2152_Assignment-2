"""
Author: Ricardo Alvear
Assignment: #2
Description: Port Scanner — A tool that scans a target machine for open network ports
"""

# TODO: Import the required modules (Step ii)
# socket, threading, sqlite3, os, platform, datetime
import datetime
import socket;
import threading;
import sqlite3;
import os;
import platform;

# TODO: Print Python version and OS name (Step iii)
print(f"Python Version: {platform.python_version()}")
print(f"Operating System: {platform.system()} {platform.release()}")

# TODO: Create the common_ports dictionary (Step iv)
# Maps port numbers to their service names
common_ports = {
    21: "FTP",
    22: "SSH",
    23: "Telnet",
    25: "SMTP",
    53: "DNS",
    80: "HTTP",
    110: "POP3",
    143: "IMAP",
    443: "HTTPS",
    3306: "MySQL",
    3389: "RDP",
    8080: "HTTP-Alt"
}

# TODO: Create the NetworkTool parent class (Step v)
# - Constructor: takes target, stores as private self.__target
# - @property getter for target
# - @target.setter with empty string validation
# - Destructor: prints "NetworkTool instance destroyed"
class NetworkTool:
    def __init__(self, target):
        self.__target = target

    @property
    def target(self):
        return self.__target

    @target.setter
    def target(self, value):
        if value == "":
            raise ValueError("Target cannot be an empty string.")
        self.__target = value

    def __del__(self):
        print("NetworkTool instance destroyed")

# Q3: What is the benefit of using @property and @target.setter?
# The benefit is encapsulation and data validation. 
# It allows you to protect the internal state of the object (making __target private) while providing a clean, 
# interface that runs custom logic—such as preventing the target from being set to an empty string—whenever the value is updated.

# Q1: How does PortScanner reuse code from NetworkTool?
# The PortScanner class uses inheritance to reuse the foundational logic of NetworkTool.
# By calling super().__init__(target), it inherits the private __target attribute and its associated validation logic without having to rewrite the constructor. 
# It also gains access to the @property getter and setter methods for managing the target IP address.

# - scan_port(self, port):
#     Q4: What would happen without try-except here?
#
# Without the try-except block, any network-related error (such as a refused connection, a host being down, or a DNS failure) would cause the entire program to crash and terminate. 
# By wrapping the socket connection in a try-except, the program can gracefully handle specific errors for a single port and continue scanning the rest of the range.

# Q2: Why do we use threading instead of scanning one port at a time?
# Threading is used to implement concurrency, which significantly speeds up the scanning process. 
# Since network requests (like checking if a port is open) are "I/O bound," the CPU spends most of its time waiting for a response from the network; 
# threading allows the program to start multiple connection attempts simultaneously rather than waiting for each one to time out or succeed individually.

class PortScanner (NetworkTool):
    def __init__(self, target):
        super().__init__(target)
        self.scan_results = []
        self.lock = threading.Lock()

    def __del__(self):
        print("PortScanner instance destroyed")
        super().__del__()

    def scan_port(self, port):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((self.target, port))
            status = "Open" if result == 0 else "Closed"
            service_name = common_ports.get(port, "Unknown")
            with self.lock:
                self.scan_results.append((port, status, service_name))
        except socket.error as e:
            print(f"Socket error on port {port}: {e}")
        finally:
            sock.close()

    def get_open_ports(self):
        return [result for result in self.scan_results if result[1] == "Open"]

    def scan_range(self, start_port, end_port):
        threads = []
        for port in range(start_port, end_port + 1):
            thread = threading.Thread(target=self.scan_port, args=(port,))
            threads.append(thread)
            thread.start()
        for thread in threads:
            thread.join()


# TODO: Create save_results(target, results) function (Step vii)
# - Connect to scan_history.db
# - CREATE TABLE IF NOT EXISTS scans (id, target, port, status, service, scan_date)
# - INSERT each result with datetime.datetime.now()
# - Commit, close
# - Wrap in try-except for sqlite3.Error
def save_results(target, results):
    try:
        conn = sqlite3.connect("scan_history.db")
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target TEXT,
                port INTEGER,
                status TEXT,
                service TEXT,
                scan_date TEXT
            )
        """)
        for port, status, service in results:
            cursor.execute("""
                INSERT INTO scans (target, port, status, service, scan_date)
                VALUES (?, ?, ?, ?, ?)
            """, (target, port, status, service, datetime.datetime.now().isoformat()))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        conn.close()


# TODO: Create load_past_scans() function (Step viii)
# - Connect to scan_history.db
# - SELECT all from scans
# - Print each row in readable format
# - Handle missing table/db: print "No past scans found."
# - Close connection
def load_past_scans():
    try:
        conn = sqlite3.connect("scan_history.db")
        cursor = conn.cursor()
        cursor.execute("SELECT target, port, status, service, scan_date FROM scans")
        rows = cursor.fetchall()
        if not rows:
            print("No past scans found.")
            return
        for target, port, status, service, scan_date in rows:
            print(f"Target: {target}, Port: {port}, Status: {status}, Service: {service}, Date: {scan_date}")
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        conn.close()


# ============================================================
# MAIN PROGRAM
# ============================================================
if __name__ == "__main__":
    pass
    # TODO: Get user input with try-except (Step ix)
    # - Target IP (default "127.0.0.1" if empty)
    # - Start port (1-1024)
    # - End port (1-1024, >= start port)
    # - Catch ValueError: "Invalid input. Please enter a valid integer."
    # - Range check: "Port must be between 1 and 1024."
    userInputTargetIP = input("Enter target IP (default): ")
    if userInputTargetIP == "":
        userInputTargetIP = "127.0.0.1"
    userInputStartPort = input("Enter start port (1-1024): ")
    userInputEndPort = input("Enter end port (1-1024): ")
    try:
        start_port = int(userInputStartPort)
        end_port = int(userInputEndPort)
        if not (1 <= start_port <= 1024) or not (1 <= end_port <= 1024):
            raise ValueError("Port must be between 1 and 1024.")
        if end_port < start_port:
            raise ValueError("End port must be greater than or equal to start port.")
    except ValueError as e:
        print(f"Invalid input: {e}")
        exit(1)
    # TODO: After valid input (Step x)
    # - Create PortScanner object
    # - Print "Scanning {target} from port {start} to {end}..."
    # - Call scan_range()
    # - Call get_open_ports() and print results
    # - Print total open ports found
    # - Call save_results()
    # - Ask "Would you like to see past scan history? (yes/no): "
    # - If "yes", call load_past_scans()
    scanner = PortScanner(userInputTargetIP)
    print(f"Scanning {scanner.target} from port {start_port} to {end_port}...")
    scanner.scan_range(start_port, end_port)
    open_ports = scanner.get_open_ports()
    for port, status, service in open_ports:
        print(f"Port {port} ({service}): {status}")
    print(f"Total open ports found: {len(open_ports)}")
    save_results(scanner.target, scanner.scan_results)
    show_history = input("Would you like to see past scan history? (yes/no): ")
    if show_history.lower() == "yes":
        load_past_scans()
# Q5: New Feature Proposal
# I propose adding a Service Banner Grabbing feature. 
# This would involve "asking" an open port to identify itself, allowing the tool to display the specific version of the software running (like "Apache 2.4.5") instead of just the generic service name. 
# This provides much more detail about the target's security without requiring extra manual scans.