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



# id 1 paa-gta:

"""
Public:
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAnwYDn1Io6C4awta8VZUA
H51tfR7GYf/Z/Go0LAqn3DeMOqDYMseGXWyyYdM2+1zSplLbFA24i0eBHJ08Li9i
XJcvle7m6EVySVFuv5QTTM7iL+UhxEGjcUgaHWb3m5CCKPiz+mg6XPqmehoI3rsO
s+UGLrjnHcltPfVJCmQArMYMYgB4fwqUndw57ipNKPfOIorIi6Hc4gy/cPiZg8Xf
GZPRLKVxziyVa+dbQNC+prVwm6NlJoz/R9iGVG8iwOe7Ez6rLjb6yAXfk+LZ7mmE
HvaGoZeSV75IuOUPJrHXGtzbI6SjBNZ2M/mMBonK7kBo50djvJq8fcmVQ2iayl8W
xQIDAQAB
-----END PUBLIC KEY-----

Private:
-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQCfBgOfUijoLhrC
1rxVlQAfnW19HsZh/9n8ajQsCqfcN4w6oNgyx4ZdbLJh0zb7XNKmUtsUDbiLR4Ec
nTwuL2Jcly+V7uboRXJJUW6/lBNMzuIv5SHEQaNxSBodZvebkIIo+LP6aDpc+qZ6
Ggjeuw6z5QYuuOcdyW099UkKZACsxgxiAHh/CpSd3DnuKk0o984iisiLodziDL9w
+JmDxd8Zk9EspXHOLJVr51tA0L6mtXCbo2UmjP9H2IZUbyLA57sTPqsuNvrIBd+T
4tnuaYQe9oahl5JXvki45Q8msdca3NsjpKME1nYz+YwGicruQGjnR2O8mrx9yZVD
aJrKXxbFAgMBAAECggEACevVYoV89V1ZAJJmnh1FbHOFLvLyVA9jEXcryZqhleDm
UAsUafieRqpfJ7DGg6CrKMLPFb10Z8YehUM/C6+bnqS1DJDi2Zdpla7trqilmptm
q6/LL0QcFxd1P6Paq1s076ryiZsilwXxSHli18iKVolhnR0emDJmrSCmPa53B1Bb
p7YOCOydeDb+uvsJFV9Q8f/LQCJz1lUhaJAeEFkkt3ozcKdBiYkMnjbFJqigeDcZ
r7r9rm8DJCHBXT+8PmCCxnTsNtHH2Sfq8Ki/Fghfd27yklZAc/nD4tpVPeF3W1gr
iZit8cCnj+dlVP/uDaqbdF4JXFCQZanM768euSG2sQKBgQDR8MdcOYPiJb3+hwnb
mhtSp3svjnSbrLyYOvXW+k5hHOf+KpPwtytN/bbUU+IquEJFRVRW6iUAAa3l9nPS
oE7Hadf+N2+m8ySC8gacZQL3DrwYV0/LtzzWTsJUD3WmFqz7HZSJCDLECwF7K9RM
S0ad+Ud957j/n74kABe+NqLatQKBgQDB6YBAkk8W+GDqftrxChnuPgQbyZahaFfK
0QyY9y3jmMfhCsJOJ0NC3+nZD0mzKyGL7MhmoarIVvflcTZvCM4ZTvqJOrYxYkku
I5AHFEIgkiqvExWXP2X0KwqiqL7MZZ+YiWglOtJKPPHKPGGPwTDp+HjI9i4IDHlR
dSaK4rEF0QKBgErBGbvVHwjft49yNihj72a3DD4a05q7H0x1ciRibJZX3KO8NYF5
N4pF1Vw1okrj4XUZArcQGKyv7GP+Ja/SNTr8jVSQGMmxukaGN6Ros22VaZShQmCf
lqIY2UllV9cUK/QezE0fBjSYVqatLKMeCr8ljDdg05byIppfDhVFDyghAoGBAKRV
9FhE5nwsEU6KJZjDm8g5jJfUFzFBUa3Tzt5QFPbewv5odNVxFuK1CuTmvOn38p04
FXpNJoRUmBA+Cwi8qJXwRglI1aEyj5xnjSdCtuwNk9j9zn14wDnWxFOnuNNWiJPo
V3e9yvwZfDyNQY1oB8Exz4NYhxhRIfuz0e9AQRARAoGBANCaSncakzlOgGEZ/vq9
1fc3O8TMqT++A8bNo4ezcVxr7kMU5PETfLhqMIyp1FQTeC5DYWYYotDR556xRRWJ
WAHjOryEq1hgojpm2EWurh9yoaE8ifhWGfE16iAVwqwfMIgHx8EmhnsrLERna0Tp
7+yA8fT59ev4Z5n54c82/jWL
-----END PRIVATE KEY-----
"""


# id 2 paa.gta4:


"""
Public:
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAt1IU+dTUcDSv/5bneO4H
agGZkmKA4Budyma/Wszi4n4JGPGkfKqCRoCf/dEqJVK3kz4bhrX2ymDNAHzo+ZS4
TZTjAdSEH+S+YvER/YOPN1bWvX5oQR2TRYZTdMa8gtLFHVQrbOXUrrdtMXaQJE+S
LLogBjscQ/mLcoEIfR4vP4VW7hg2f6FxpAPxYmvAs5wMAUiy5BRSfur7ejvDwylm
1S8/mT4tWy6HvGBAmqmgUIgxUNSdZiAqB0+ycqVFl3IaV9VG9j0ux8FU1mBXMTQZ
/45wd64SED+84ulwDaTUcmvxO8KL18U/ZMPxHJ3rLADONOcQbl71/AJOjQw2g7F2
jwIDAQAB
-----END PUBLIC KEY-----

Private:
-----BEGIN PRIVATE KEY-----
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
-----END PRIVATE KEY-----

"""

# id 3 andrey.ivanov53563:

"""
Public:
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAyU5m9tt+nyqwoy3UlmNa
59KElIDx9Pl3JpoZRoJjhasgTa5kM5hTJLKhiRb1beC+nrXLgBrpGtDEhPnNOw9I
Z+ZGLvzDYS6Ou7iMM+AK8xZi1LzNlWL75brvD18Eostexm0F2xdHsmFPua8sF6A8
EP7NfYoEe1HD9PZtSpMnXJq2JYt8n2796AbTEzVUZFSI2FFJR2oHTOcuxme8gGa0
H+a6V5dND8n0q52uriWVKeSc/VEsNEXvAPXkMM6WbUc4MItPOcNVD+KvV32g5VNY
AlNMzUYUB6autI2Oa4XHUBDK4eWQTalC0MGDJhFxS+ZjzZxRS4F+psiWx3Am8O6y
/QIDAQAB
-----END PUBLIC KEY-----

Private:
-----BEGIN PRIVATE KEY-----
MIIEuwIBADANBgkqhkiG9w0BAQEFAASCBKUwggShAgEAAoIBAQDJTmb2236fKrCj
LdSWY1rn0oSUgPH0+XcmmhlGgmOFqyBNrmQzmFMksqGJFvVt4L6etcuAGuka0MSE
+c07D0hn5kYu/MNhLo67uIwz4ArzFmLUvM2VYvvluu8PXwSiy17GbQXbF0eyYU+5
rywXoDwQ/s19igR7UcP09m1KkydcmrYli3yfbv3oBtMTNVRkVIjYUUlHagdM5y7G
Z7yAZrQf5rpXl00PyfSrna6uJZUp5Jz9USw0Re8A9eQwzpZtRzgwi085w1UP4q9X
faDlU1gCU0zNRhQHpq60jY5rhcdQEMrh5ZBNqULQwYMmEXFL5mPNnFFLgX6myJbH
cCbw7rL9AgMBAAECgf9f9rsykHA4l6E6d6hz4Uu5mfpLH6NMGyoeH0QoYonnmxit
oKYQGeX+8SjpABKw9gY3tjcvH32dyufkBh2yYnkrrBqhmmcTRXcn8lH3fH27xr7z
+fmQ+G2mlkVMjpL/zRqSVaG57VVKR6NNnGVetoQTRz0Q9CbMVCRbDs+8KZGj62vH
2hndmqVO8AcqMFkiAY7oQESrFZoSaND/diPq1eq1+uDpTUBeH84pXvIjcUO9R017
lAi7QxWLBsfq/Xg/SZO0+r2hnvim6fjdSZ6izpaWQec7/wT5D8dtUPAefT5xYFk2
bCyj6U7MxYowYjEKDSvQtcb0lV1aFbQTyxqtyzECgYEA4z4hxnJXJ/afz8KEX9gy
zjIZzVsQmOg4pGQAHyPtFmYqpAy7sZefNl6STQ9i/uU/pS1LPUYoq9HMSfZSOmgL
2RUaoCpFCqF/+6RpW6rZ3lreQMHqjAxjtDHu3iPzBt+bj1EdmA6OzQvyChb6sPg7
reSWGVVnRiopY6hCIMJL6cUCgYEA4sgFMIQKQeqH84dsBtUhfVo2Tyc7k9Ly3pFD
GWE0f3QU4+781Dxmusv9Mrmee+hV+Vy89m3bKxDqzHKiwdNliG10bJbXyt33N4NB
Z4RKNcg28YSCSlNbOBfr8PXBG5busQLwygvFnLKm526dQSysH/ZX/w6ZWPmz0Y+8
csGHD9kCgYEAuQ7xPIYDOlVbAjvbx53uigM9BgKiOpPrBN03SCTewD4FfcGs3Myo
aQONS1o7eW9CbIa9XjITjxF0t8r0XgI7m9bW7xZdUXICIvFap780XCNOGhiRpOm2
DJoZeCh4kuFo8sbRPfKlEpEm1FawY4xUNaIRJqJpTzeoqzLsX3c7kS0CgYABwSBh
JrRZnDHfDW4lg2KV8Ku44wnP8/LTC/aj7J+WWNSMit3D2o/E5C0aRltWhA6eNjxz
/5eRdrkKSdy+eR8w9f/Pkz8qH5t4/3fzEA/u6JScO7UyVADBp1W48H3E89722Zn5
RiwKMUufQLjQt0LBoIs/uuIu0Qe2GFGR5bNgyQKBgDGhlrcXjnFKc+AAshB/kBMj
mXcMm/C9Dt/1zcUM0k5owgjRZWzn6o7MnbZ+D9XLE7k9qANp4uuIdm7DCWU55iOM
ocPO3zMKp0IHtZh/t1yRVJiTP6NE5Z7a7yZzSdq6rGtKTsG9fFP/tPh9I7iJg+6r
LZHxLj/PgZTs0XaRuCxT
-----END PRIVATE KEY-----
"""