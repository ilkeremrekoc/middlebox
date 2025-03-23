import os
import re
import matplotlib.pyplot as plt

def parse_ping_file(filename):
    """Extract mean millisecond delay value from filename and avg RTT from file content."""
    match = re.search(r'ping-result_(\d+)\.txt', filename)
    if not match:
        return None, None
    mean_delay_in_ms = int(match.group(1))
    
    with open(filename, 'r') as file:
        content = file.read()
    
    rtt_match = re.search(r'rtt min/avg/max/mdev = [\d\.]+/([\d\.]+)/[\d\.]+/[\d\.]+ ms', content)
    if not rtt_match:
        return mean_delay_in_ms, None
    
    avg_rtt = float(rtt_match.group(1))
    return mean_delay_in_ms, avg_rtt

def main():
    """Find all ping files, extract data, and plot results."""
    ping_data = []
    
    for filename in os.listdir("ping-results"):
        if filename.startswith("ping-") and filename.endswith(".txt"):
            mean_delay_in_ms, avg_rtt = parse_ping_file("ping-results/" + filename)
            if mean_delay_in_ms is not None and avg_rtt is not None:
                ping_data.append((mean_delay_in_ms, avg_rtt))
    
    if not ping_data:
        print("No valid ping data found.")
        return
    
    # Sort the data by mean delay values
    ping_data.sort()
    x_values, y_values = zip(*ping_data)
    
    # Plot the data
    plt.rcParams.update({'font.size': 22})
    plt.figure(figsize=(8, 5))
    plt.plot(x_values, y_values, marker='o', linestyle='-', color='b', label='Avg RTT')
    plt.xlabel('Mean Delay (ms)')
    plt.ylabel('Average RTT (ms)')
    plt.title('Average RTT vs Mean Delay')
    plt.legend()
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    main()
