import subprocess

def count_connected_iphones():
    try:
        # Run ioreg with device-level output
        result = subprocess.run(
            ["ioreg", "-p", "IOUSB", "-l"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True
        )

        # Split output into blocks for each device
        device_blocks = result.stdout.split("+-o ")
        # Count blocks that represent an iPhone
        iphone_count = sum(1 for block in device_blocks if "iPhone" in block)

        return iphone_count
    except Exception as e:
        print(f"Error: {e}")
        return 0

if __name__ == "__main__":
    count = count_connected_iphones()
    print(f"{count} iPhone(s) connected.")
