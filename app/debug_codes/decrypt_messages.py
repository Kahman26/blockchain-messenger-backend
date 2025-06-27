import json
from pathlib import Path
from datetime import datetime
from datetime import datetime, timezone, timedelta

from app.utils.blockchain import decrypt_message

INPUT_PATH = Path("input.json")
KEY_PATH = Path("private_key.pem")

LOCAL_TZ = timezone(timedelta(hours=5))


def load_private_key() -> str:
    if not KEY_PATH.exists():
        raise FileNotFoundError("Файл private_key.pem не найден.")
    return KEY_PATH.read_text()


def load_messages() -> list:
    if not INPUT_PATH.exists():
        raise FileNotFoundError("Файл input.json не найден.")
    with INPUT_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def format_timestamp(timestamp_str: str) -> str:
    try:
        utc_dt = datetime.fromisoformat(timestamp_str)
        local_dt = utc_dt.replace(tzinfo=timezone.utc).astimezone(LOCAL_TZ)
        return local_dt.strftime("%d.%m.%Y %H:%M")
    except Exception:
        return timestamp_str


def main():
    try:
        messages = load_messages()
        private_key = load_private_key()
    except Exception as e:
        print(f"[Ошибка загрузки]: {e}")
        return

    print("\nРасшифрованные сообщения:\n" + "-" * 50)
    for msg in messages:
        encrypted = msg.get("message")
        from_user = msg.get("from_user_id")
        timestamp = format_timestamp(msg.get("timestamp", ""))

        try:
            decrypted = decrypt_message(encrypted, private_key)
        except Exception as e:
            decrypted = f"[Ошибка расшифровки: {e}]"

        print(f"[{timestamp}] от {from_user}: {decrypted}")


if __name__ == "__main__":
    main()
