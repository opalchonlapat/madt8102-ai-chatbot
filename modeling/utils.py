import os


def os_write(text: str):
    str_content = text + "\n"
    os.write(1, str.encode(str_content))