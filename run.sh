#!/bin/bash

# Check for Python 3
if command -v python3 &>/dev/null; then
    echo "Python 3 is installed"
    # Run the JavaScript program
    cd /home/yoshiost/bible-plan-to-discord-py/
    python3 notify-plan.py send > output.txt
elif command -v python &>/dev/null; then
    # Check for Python 2 (if Python 3 is not found)
    echo "Python 2 is installed. too old"
else
    echo "Python is not installed, install python 3"
fi
