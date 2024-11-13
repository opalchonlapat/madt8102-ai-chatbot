# MADT8102 Final Project

This repository contains the AI Chatbot for Employee Attendance Assistance, a feature for HR analytics. This project is part of the final assignment for the MADT8102 course.

## Installation

To install this project, ensure that Python 3 is installed on your system. Additionally, you will need an OpenAI API key. If you do not have one, you can obtain it [here](https://platform.openai.com/account/api-keys).

Next, install the required dependencies by running the following command:

```bash
pip install -r requirements.txt
```

## Usage

To run this project, navigate to the root project directory and execute the following command:

```bash
streamlit run modeling/app.py
```

Your Streamlit app should open in your browser. If you encounter an SQLite error, please refer to the solution in the [Chroma SQLite troubleshooting guide](https://docs.trychroma.com/troubleshooting#sqlite).