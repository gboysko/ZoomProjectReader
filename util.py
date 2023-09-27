import sys

def status(message, stream=sys.stdout):
    # Send the message to the correct stream...
    stream.write(message)

    # Flush the output
    stream.flush()