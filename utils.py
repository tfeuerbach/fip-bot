# utils.py

def clean(text):
    return text.replace('"', '').replace("'", '').replace("&", ' ').strip()