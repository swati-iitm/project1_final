# /// script
# requires-node = ">=16"  # Ensure Node.js is available
# dependencies = {
#     "prettier": "3.4.2"
# }
# ///

import subprocess

def format_with_prettier(file_path):
    try:
        # Run prettier command to format the file in-place
        subprocess.run(
            ["npx", "prettier", "--write", file_path],
            check=True,
            text=True
        )
        print(f"Successfully formatted {file_path} using Prettier.")
    except FileNotFoundError:
        print("Prettier is not available. Ensure the metadata dependencies are correct.")
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while formatting: {e}")

# File to be formatted
file_to_format = "/data/format.md"

format_with_prettier(file_to_format)
