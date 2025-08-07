import asyncio
import json
from app.utils import blockchain
from app.database.db import engine
from app.database.models import UserKeys
from sqlalchemy import select


async def generate_message_template(sender_id: int, receiver_ids: list[int], message: str, sender_priv_key: str) -> list[dict]:
    template = []
    signature = blockchain.sign_message(message, sender_priv_key)

    async with engine.connect() as conn:
        for receiver_id in receiver_ids:
            result = await conn.execute(
                select(UserKeys).where(UserKeys.c.user_id == receiver_id)
            )
            receiver_key = result.fetchone()
            if not receiver_key:
                print(f"⚠️ Публичный ключ для user_id={receiver_id} не найден — пропущен.")
                continue

            encrypted_message = blockchain.encrypt_message(message, receiver_key.public_key)
            template.append({
                "receiver_id": receiver_id,
                "encrypted_message": encrypted_message,
                "signature": signature
            })

    return template


if __name__ == "__main__":
    sender_id = 2
    receiver_ids = [1, sender_id]
    message = "Это сообщение от 2 к себе и 1 id в личном чате "

    sender_priv_key = """-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC3UhT51NRwNK//
lud47gdqAZmSYoDgG53KZr9azOLifgkY8aR8qoJGgJ/90SolUreTPhuGtfbKYM0A
fOj5lLhNlOMB1IQf5L5i8RH9g483Vta9fmhBHZNFhlN0xryC0sUdVCts5dSut20x
dpAkT5IsuiAGOxxD+YtygQh9Hi8/hVbuGDZ/oXGkA/Fia8CznAwBSLLkFFJ+6vt6
O8PDKWbVLz+ZPi1bLoe8YECaqaBQiDFQ1J1mICoHT7JypUWXchpX1Ub2PS7HwVTW
YFcxNBn/jnB3rhIQP7zi6XANpNRya/E7wovXxT9kw/EcnessAM405xBuXvX8Ak6N
DDaDsXaPAgMBAAECggEACC6Mqx3ZoWxokoK8sAQHpq6NmR/2WopA/6CYV8gfNDal
10wpqDq/97+T5HMqa2IGuXajKd8DNcMeQzBQAZumoifL/e/rObUu3iGeSO9PPAwP
J4P1yTo1sXuuS9722OvpSkbQbVrQpD+hivycsFIw1vgzp7OJrmr70094/oSTXUVV
5Uv++5oDagx1xLrsVntSgKhQ6Q1LhOqNdKVyYYYG7X6KnB0wMIHQQ+7p6ODpGPal
cvo09t3DQOOQCIEEu1q1qq8bPO3I2I55umBuAn1dJ7hAq/DJ8FaD3iGqJ81HEfnQ
2ZpKxKKDHRt7uISkb+39BwmKwy8kewRx/Xwe1zANWQKBgQDdczz6LekOX1CbmJ+f
t176jhA3xnrxXwHydGKHAJUeVY3U/fbO3PQisZUlZiifh42UWxAbhU64yVvVKsbS
gvYsa0uayh3u6ILBWJLoWSn33c7J3Mznwf8lURSL7RFoNJV5rIZCyzmJP2zr+ULm
dCFbEpWiSiInAiKPQs1wX6dp6wKBgQDT6/GHcqDuPzKbcEo9vpDT1jkhova29vGq
1RuTfxCGJ84339NgcfmPr+43UVBuSQuOYHx7e5Rt8lmolkiXoZ4PldLvTFP1AuzO
Z/7vrrJhZwelia9gS5ZB6stTgElNrKZYc+qYb/ILxmodYaOT2mgTCIl2IUUnAjHt
24VgEFs47QKBgBI8jDf6Eeg6FzRJFFQd0LeHfXRqZvN7pHhn9zkw5hbSatSweWO9
tGkrAKJM0GmayyD9gs0RZFM5WdOrKyZo3Ib56wb7QA3Nnf74IVj7Bsa/wGjFQyaO
xkk3bR68ziMruWeEuqXDgKB51al1JHo/9ANA+4ua2UcnGNt9X9eyOOIzAoGBAIUc
pchrUvRzU8lY3fkskvHMlHQxVYCVWjTwyPJ7lJh/tkNYXwAsdxIu8pViiP/M9+pF
Zst1U0VAPdrsEsrTpGGrvSO8MNwsKyx3HCXW+Iq/2Yi8FCGLOOVMosxfPyv/7ziO
DuQTJNkKlyq/Yq0DOe4Cpb1CppobAdui0IMHoxT9AoGBAI+2L/sbZ+MwaRLcKJJ2
8XDLeJr4hV5TTXtEY2s7AQSJ+RxsVRfwfVXx3qEDyE7HwMlpJIPB2h6g3unY/a7J
uVvblbC3NfSqVgiBVFjfO+PFVLdfc/3f+G2iziSBaf/8kGZK9d2rZxMtmw7f+GIZ
2PmSRN4Qk2oHvFx/z09WZOHi
-----END PRIVATE KEY-----"""

    try:
        result = asyncio.run(
            generate_message_template(sender_id, receiver_ids, message, sender_priv_key)
        )
        print("\n📦 Скопируй это в Swagger `/chats/{chat_id}/send`:\n")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")



# Шаблон для сваггера от id 2 двум пользователям:
swagger = \
[
  {
    "receiver_id": 8,
    "encrypted_message": "QdcgzFhN0/hiWE/xQIvgtN25gbTVSmV5hZUiDpj0AOoJUh40KSV75uvZ0AP24TlMCC3DiR5MHPtnXEt3WRJOzBpMOGC0Z/yLT3Tzq25G38ZFl2UzdupPm6Xo/sY68HFg0qFCWt+o6UkDEsDAfNrOl6sPQTSjXvxYD1zK5v8HCczuRkF7qPw7sMZLY745yzUcSZRXOxzquE6xDmiypRycRmK9QsW8xykPqD64T9JnQAL2MZiZi+XjiHpR9kpelVNam2jfWjQUrKU0fu/J1xuCoR4LwQAWTzDGvX1j3FYnGMxzgDOxtOYHFAkdSN+J8tsWU5JHdTS4p11msFv2FeeFwA==",
    "signature": "oHYXWdC6i33rMT63cmw2GF9lFdF9RQxuDugzq+31rG0a36r4jgqeOzBzzHk14ghDPMFnTC8wLX8tIktlNXv+b7Pe9PUJTYwdbNlIy7/RLGMWvS0UG4W4UqdJaJAPAE0/jNuzhWUKvls/RJPL3ZOnzXguffQY4ADmH2u/CeiaaY5gOGTSMfyAzjbMc2h91dYl7KPBq8UdskCTqwH/Hbvib5UweCKD/OQTU5qT1TP8E//uw8lvvI/AHCT2Dn8BCKKGcxPsPAURgtIeVh0oRdwwWXNUq0iB4KBChHSYp44GoxXTTi94wyKkd/Z0ckCgEDmhG/1F4nZyJQZwri/dj/D6ig=="
  },
  {
    "receiver_id": 2,
    "encrypted_message": "Aujx+GxoARlS1mLgp32PFNkjQbTk0xn66DW03C5BnJzzNQQLYJvh21w0pQmriOXbgk6BA/rFCOwSrcVOJ4iqZT7sCxNPim8tu7Q7HeWcK5Qo8wd60AroSYJtGyoiSWFAYuXgfG2+t47nL0+KDm+dbsbbnTN3atdtw1UJRYSnRDuqmbPoUUBHaX3jtLR/ZGBibiM1Dw+EUQT/oxajuDGjeNf1Kb3KNP6huvhEkBC5aJVo+fpJJZyHCsz8MwLoEe6Hu/ExaR3jzWx6ACBQMdED5Zp/DHIZN5SUdcXg/sRiiI+epNJxpR4bV4+RoXnDCRU1am9yaneuzwQhh5/OqSfgrA==",
    "signature": "oHYXWdC6i33rMT63cmw2GF9lFdF9RQxuDugzq+31rG0a36r4jgqeOzBzzHk14ghDPMFnTC8wLX8tIktlNXv+b7Pe9PUJTYwdbNlIy7/RLGMWvS0UG4W4UqdJaJAPAE0/jNuzhWUKvls/RJPL3ZOnzXguffQY4ADmH2u/CeiaaY5gOGTSMfyAzjbMc2h91dYl7KPBq8UdskCTqwH/Hbvib5UweCKD/OQTU5qT1TP8E//uw8lvvI/AHCT2Dn8BCKKGcxPsPAURgtIeVh0oRdwwWXNUq0iB4KBChHSYp44GoxXTTi94wyKkd/Z0ckCgEDmhG/1F4nZyJQZwri/dj/D6ig=="
  }
]

# Шаблон для сваггера от id 2:
swagger = \
{
  "receiver_id": 8,
  "encrypted_message": "mY27dkHn4FOjoi0pOWAiwVNcFa6LGfon1oYbw2eQTZpmLseUNlTLcSyKQR63PABJzAxVVYFSThEzfs2nMOiiTbF7H0gn3nlZEgrQmiiw6DxFK14P85r3TwZbC8ZyVhlGu0j5qK75qOv9n76cFg8V0qD2R56rBsTeoF1p35FKxpyaS7jyJbmLSR1hdXYb1fgCg2WpF80cmhhGOTiRKNerpjlua9U2QKWNmIcivYlxytiRUZ1/mI7e6cqW+6f0xgN5cs8HoSKVujOyHg4KmOzs3qRl2ruwLVwaEj7k4aJFd2tcMSIa+mMNtDuptXB9DEiiBf6zsA3RZAX1rp9+8Ko0dg==",
  "signature": "X5pvcuwB9siBhg5sKZtW+bUkSw2OLYkoxsK+SsVW25YY5awbv5bkdYkzAod7X8CxtUVplwMvk+Y9sq9URusWDP1CvDHl6jI8AorgfJ0cK/0qwq/Zpe/HerzLhSkGhMYXv07l5aaQfAPHGJJG1C+I879+LfDw6AL7egoQanHc8X68HthnZGItujP6q0qFrzauhB2Kk48EhgGq81QgSTrd/vtJ6xKmatZ5SO3eoCCz0KnH3j6opaV7TVzD6uzwqUOdQgTfwObNgQnmO2kqDBb++8WQE4KDy8zURFa5t2yeKCOGcPJA8d6RCD2Mimc4caHDoYeCbvdZGbAfeaUNVykCMg==",
  "original_message": "Это сообщение от 2 к 8 id"
}

# Шаблон для сваггера от id 9:
swagger = \
{
  "receiver_id": 8,
  "encrypted_message": "VfOnxUp4mmL8nprnhrqL8RInPHsYoBYKa1a66EFxa4iWq+QVz/IRfgTAGe062d0TWTKVeoJyh6HjehYChx8J2VDTWC0S0zYfCofAyBvJE5DXMTeJ3TkypwPWCLRkW0s7glJmL7KxGklSQ4dqdT+oowdZoYp0Cvh+mbYd2k87H4uK1TlGVIjkmuExfaFfwLv8E06BKopXQJxt3BjUmtkT5VRb4xrP0RythDmPBA9lTc2tM0y3AWmFOEkpRvc0/K2CPhzOFKWSfgmtLr9t9iwKgXRF1jYsb1GKhDh9zJmUOw6GCFvVHbJgLm/6v+bh6uxChf+gk6tet2nxje36PkzM9g==",
  "signature": "Vi/T7HJ1mOx6QErFLKBJ5mlTAIxnmoGxhGMw5mWGn5Dg1a7dCm4ck2bV5FDQwpYh6uqSBsVoiDuLKG7dG0KHoedsijGxuaHwW1V79x2HXbDA6IVLGSBnh3jDCwI8lKYzQYnpoauRbxQS809MP37qvQwr4Glqqz2YoesXzrCVTe1O3xnYSAqMYse2w3BuSqmc2tOiNXS//1w2kbei3zUTM672TXUnSMuiZ7Tne6HXbviu070Z3FFvPF3OvqaaU4+Ypora6EETEtqw7sp9m9n/OIWPrcI7uBofVnyPF8b4tOlnAg9eJhKbRQw3QGBazw1ZTkrm0b2B3As2Vg3rfSO4+A==",
  "original_message": "Тестируем работу!"
}