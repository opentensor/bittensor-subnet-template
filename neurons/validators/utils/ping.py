import socket
import time


def ping(host, port, attempts=10):
    times = []
    for _ in range(attempts):
        try:
            start_time = time.perf_counter()
            # Set up the socket
            sock = socket.create_connection((host, port), timeout=0.5)
            end_time = time.perf_counter()
            times.append(end_time - start_time)
            sock.close()
        except socket.timeout:
            times.append(float('inf'))  # Use 'inf' to indicate a timeout
        except Exception:
            times.append(float('inf'))  # Use 'inf' for other exceptions

    # Calculate average time of successful pings
    successful_times = [time for time in times if time != float('inf')]
    if successful_times:
        average_time = sum(successful_times) / len(successful_times)
        return True, average_time
    else:
        return False, 0  # Return False and -1 if all attempts failed