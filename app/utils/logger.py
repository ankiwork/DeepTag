import datetime


def log(category, message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    print(f"[{timestamp}] [{category}] {message}")
    print("-" * 150)
