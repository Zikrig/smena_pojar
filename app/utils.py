from datetime import datetime, timezone, timedelta

def get_moscow_time():
    return datetime.now(timezone(timedelta(hours=3)))