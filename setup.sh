#!/bin/bash

# Setup Script for Open-Agentic-Investor

# Step 1: Ensure Python3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Python3 is not installed. Please install Python3 before proceeding."
    exit 1
fi

# Step 2: Create a Python Virtual Environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "Virtual environment created."
else
    echo "Virtual environment already exists. Skipping creation."
fi

# Step 3: Activate the Virtual Environment
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "Failed to activate virtual environment. Please check the setup."
    exit 1
fi

# Step 4: Install Dependencies
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies from requirements.txt..."
    pip install --upgrade pip setuptools wheel
    pip install -r requirements.txt
    echo "Dependencies installed."
else
    echo "requirements.txt not found. Please ensure it exists in the repository."
    deactivate
    exit 1
fi

# Step 5: Finish Setup
deactivate

echo "Setup completed successfully. To activate the environment, run:"
echo "  source venv/bin/activate"