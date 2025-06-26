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
    sender_id = 8
    receiver_ids = [2]
    message = "Это сообщение от 8 к 2 id"

    sender_priv_key = """-----BEGIN PRIVATE KEY-----
MIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQCdogQRx5DiN5cd
R4s48WbpJk+5Oe9AugRBjPIDynDYC3gjDhoAarZvZsEgJlBPK25Pl8WlIDnaKnOc
0W7Qm5QZR9lRQw7tfsxKijJ/5lbAupbK5F+RmgxxWi6FDMZ5GomHsq8B827TnOCX
5/AFl44qyhM3fF1nncHVRs93nrsx2x6pEwQNQdsExsH/TGkk0R6U5p8B15ZJ3M7P
KQcBpknbzfGDsMV+HbhuBy2LMzFHKFGY3ZZc4aBVFIGYpn0/niCgUaHJNJTMc7YC
AhB2O6cbdThUgXJREq9Fy8uuucvuFPriQie2/OYqw4OS6mbaQDZ4EqT4wVruymVI
zY/rTAeHAgMBAAECggEAGiPNq0nInQ2H5HtCkJOjiQKT54zpFSGOZsph2xQSiMPE
zSy0+MsOwW7XlCZrsefrV+KSDB3Jyi5jqVEnoGCe+17pSur6X5Lj0MaVtOpJtOsc
P2gF8HC3Iy2dF5jfPsznmpZHJDqDRISNeqij1Qw6r0jUTU1fyzjOIGPThVbQBxEN
l1vPsqJU0h+8D0RiDVaqp8dTlxMXCVhlDm2p150NVPQWkeT4KRIaP0/JWoDNvpiJ
VLYtpU0+qr7ZDZdl1e7/ahO2tD8Lc3bBR53Ow3Jgg8iKu4V1s4UG2n0tMM+bSwtF
TA4SI9E8q+4oBmWcmeodmujCNau0zJguEYCQ5nkeTQKBgQDRmjqu4ragFecDeyL2
hIORwXifCXRlivxeRTmjGd7ZotwoM7BOJe7EfP6U/g3//5ry6tRTduJR6KPyDKkx
CDBri5kKOA3sScCvDl8RNbpXpEbr0844T6H1S1vNIBKTIC5rD9yTB/HSQfHLgBlE
2GeMeZVWvN+Q1HNi40BiTT7FHQKBgQDAhsUKCFAQKi2ggZV6jCdXwo9tuAZk0jCs
Pbkgi4yK3CUA/qqzy6G+jvFUqSg/uLcdxSDiHLtOODxhsm3+fIuIUsCLGV45vUoW
oI2ymXfMeN8hqkR+XGlFKDWje68PQJiUjocmqFAqxDCtYMB4mvsqNx/ofYyv6eDa
kkbZ0iAR8wKBgBAc2RIEn6FizaV429EzkqGry8f+BBKiQpBEpg+ht33nhSEaCB2Z
0OcN7MwrU4wwbArsfnIEG5XMWn4K9x6r0H0T+CnO8VMOwF80rZ43ESIXoNQULjAp
/vtKVb5JDuR8ftUAHSa4X6CYLSxFpquiLyOfXRmT32PU0SHy8kocQg0JAoGAPqJZ
rhbgPTILoAEoaTL5hbKVSOOqqNg833xBIxZjRbWzECzJyi6AU2dbmehiYMCuSjAc
r5MbWKow8rPC1x0bo+EQJPC+19f+J3haQPVupQXZybEEEXvs/4PCV4pgfHzOZt4r
l+cAFbm4AF/Oni4Fckl2xwM5Zu2WqmUWSbzzlAMCgYAbZ9gHVQSwdjF7vRGScRu9
B6pcDfgPBiq1xzVu2rV0Hv49u8z6gtGTe/alpgQcnXIja2eMyrgwbSA7J9VusLhi
NiLHcXoEm5ZhXsjgJtAlIqMVLk3J2olWJDhUldZrx9ju0xUSXmZSdKJhv/sC3Jy1
197mr0SkTveqRU/UO5HluA==
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
    "encrypted_message": "mY27dkHn4FOjoi0p...==",
    "signature": "X5pvcuwB9siBhg5sKZtW+...=="
  },
  {
    "receiver_id": 9,
    "encrypted_message": "Qlhfd0h4OG84SnAxZ...==",
    "signature": "X5pvcuwB9siBhg5sKZtW+...=="
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


# private id 2:
"""
-----BEGIN PRIVATE KEY-----
MIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQC4yp6s+jUhuZw0
kFMu3OGmB2C950Nzz9YU5tDWqRr4YAtjq2JiDk5kIjtMfni2O/s/6wdm5gup9DEi
1YyzELoUzPC7q+urEFXmzurSH1wzMPFRXQ1J5l8l3/qM0O+2dLOqIIRrOstP9OY2
NA2swQrXbFTbQyvm75M16lh1ZxghzJE5ER/Gf8tKtNfLJ2Ea0fUw4RgrvYIO9po/
Tzs9pu0+jE8U+SzqRDlJ8aQh/4DzUguGS/ZxrJsRtPc2vozyky7eWV+2GklbDKoq
zHDAjGcYE57VGVwI1Dt+eoGEs1MuXF/Bm88Qr6MzH2inw9TqmpFYD7g7x9bfSdFk
AvrXSsdJAgMBAAECggEAKPCfAfS3A79C97RH8Zh3F5kH2lrbq1NO+zd96ijx9DgX
HeBQ/idsP6wD1jko1jrouasA60+pIuCaaDzGnL9mcohLB1EZ9765QVbzWFUhUKgV
trB2arpytwnt0PfTO+mUCmuE2treQ1sfC8AxjWYBWGPEUwWJOvM1+ppuOah7BLWU
zHrGrUrrfFQQmkEoYkehJ/hr1XmRTGJTCKuAhD+DTVFzbeJ32n2oRh8jH9nWcMY7
bxf3qLf0Ezz7tVzswTgJBDo/6KRQBU2mwNaTuFcYq7wu4oy/DHWQQ5qZN+uFvXqS
xxgT2fFCV0AKrGdZA3m5D3EW6IerWD6ECgDEBUQjVwKBgQDdv58R/gIU4wSugagy
X1i4GW9+sZGe6iCQhxtyalv0lsqaHpUWZwpb8AEfBoAMcemLz75oSnQ4IT0Zy2j7
ZFjMrjtTVAiagJQGRmGXo98VimAEePMaU5U2Ef3b+SF2Pn9q5IgJ3V/SB7tIWHu+
O20Le0/WKHPXW2bxb4ELXn3a5wKBgQDVVaS91QQ6Eok9tR+b2IDo0fu10BUchr3O
EolUO6Bi03yvJaChU2jJPx1lgNOYmpv85kh2QmEpsgZ+3U06ENP3kN2GDQdUms9Q
wpXpcvN00cU5Nx79o1tpp9q9dkIGY3VQcn9iiNBIoZy0+Gb2d0XqV1IhQXfhXe2b
fed3Pgy2TwKBgGNyP1VjU+2oDf5w2UyV5ATUK2NnIQZiu231mYKLXmfnhD7v/i6I
0WV/0hDm6mAqafGwnhTJZyuRBITf61nqm8RXUvXA1wbrKPdTcwr9i9tuLjdzQpsI
5v7TvMR9CturlZsLmFLMO9/GZeBBBmW+4t1mVNyXUbRAIn+eYQIHQ2v7AoGAaFQT
1so/4O6Ds2vKY3rDwBhA0q9KQ8MZO5gRFOJ8Exh+F2F9ZqfVzOVSyPrxf+XMdydf
NIZN4ggv6Qbs54KnRqDP1Oi2NwfmbwZaLeqLaQvVOZ/dRgkHgWoXLSSSMXGeQ5Na
/KMPyRVP/6ijIdE+ndXKUn0j1VEMDEjMU6JCsT0CgYBk/R+UCenDjRRu8tnvzAB6
pnsxVzJ40+wAkX9/MGIcq4I7fJ7T2nCVlmBx4mFzXMVZ0l+Rrp8nO5KS9VlHoB4c
v4ZlxoUvGrcdrtbp98eI4dimbdiKtD6BadaQ+RqpKxtAb8uLFIYkThAAOOccRYiF
/fkmB+dcDxC924MPKArzxQ==
-----END PRIVATE KEY-----
"""

# private id 8:

"""
-----BEGIN PRIVATE KEY-----
MIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQCdogQRx5DiN5cd
R4s48WbpJk+5Oe9AugRBjPIDynDYC3gjDhoAarZvZsEgJlBPK25Pl8WlIDnaKnOc
0W7Qm5QZR9lRQw7tfsxKijJ/5lbAupbK5F+RmgxxWi6FDMZ5GomHsq8B827TnOCX
5/AFl44qyhM3fF1nncHVRs93nrsx2x6pEwQNQdsExsH/TGkk0R6U5p8B15ZJ3M7P
KQcBpknbzfGDsMV+HbhuBy2LMzFHKFGY3ZZc4aBVFIGYpn0/niCgUaHJNJTMc7YC
AhB2O6cbdThUgXJREq9Fy8uuucvuFPriQie2/OYqw4OS6mbaQDZ4EqT4wVruymVI
zY/rTAeHAgMBAAECggEAGiPNq0nInQ2H5HtCkJOjiQKT54zpFSGOZsph2xQSiMPE
zSy0+MsOwW7XlCZrsefrV+KSDB3Jyi5jqVEnoGCe+17pSur6X5Lj0MaVtOpJtOsc
P2gF8HC3Iy2dF5jfPsznmpZHJDqDRISNeqij1Qw6r0jUTU1fyzjOIGPThVbQBxEN
l1vPsqJU0h+8D0RiDVaqp8dTlxMXCVhlDm2p150NVPQWkeT4KRIaP0/JWoDNvpiJ
VLYtpU0+qr7ZDZdl1e7/ahO2tD8Lc3bBR53Ow3Jgg8iKu4V1s4UG2n0tMM+bSwtF
TA4SI9E8q+4oBmWcmeodmujCNau0zJguEYCQ5nkeTQKBgQDRmjqu4ragFecDeyL2
hIORwXifCXRlivxeRTmjGd7ZotwoM7BOJe7EfP6U/g3//5ry6tRTduJR6KPyDKkx
CDBri5kKOA3sScCvDl8RNbpXpEbr0844T6H1S1vNIBKTIC5rD9yTB/HSQfHLgBlE
2GeMeZVWvN+Q1HNi40BiTT7FHQKBgQDAhsUKCFAQKi2ggZV6jCdXwo9tuAZk0jCs
Pbkgi4yK3CUA/qqzy6G+jvFUqSg/uLcdxSDiHLtOODxhsm3+fIuIUsCLGV45vUoW
oI2ymXfMeN8hqkR+XGlFKDWje68PQJiUjocmqFAqxDCtYMB4mvsqNx/ofYyv6eDa
kkbZ0iAR8wKBgBAc2RIEn6FizaV429EzkqGry8f+BBKiQpBEpg+ht33nhSEaCB2Z
0OcN7MwrU4wwbArsfnIEG5XMWn4K9x6r0H0T+CnO8VMOwF80rZ43ESIXoNQULjAp
/vtKVb5JDuR8ftUAHSa4X6CYLSxFpquiLyOfXRmT32PU0SHy8kocQg0JAoGAPqJZ
rhbgPTILoAEoaTL5hbKVSOOqqNg833xBIxZjRbWzECzJyi6AU2dbmehiYMCuSjAc
r5MbWKow8rPC1x0bo+EQJPC+19f+J3haQPVupQXZybEEEXvs/4PCV4pgfHzOZt4r
l+cAFbm4AF/Oni4Fckl2xwM5Zu2WqmUWSbzzlAMCgYAbZ9gHVQSwdjF7vRGScRu9
B6pcDfgPBiq1xzVu2rV0Hv49u8z6gtGTe/alpgQcnXIja2eMyrgwbSA7J9VusLhi
NiLHcXoEm5ZhXsjgJtAlIqMVLk3J2olWJDhUldZrx9ju0xUSXmZSdKJhv/sC3Jy1
197mr0SkTveqRU/UO5HluA==
-----END PRIVATE KEY-----
"""


# private id 9:

"""
-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDaqaQgwqTabyUD
7GVlVijgMVtF5yzDpPwU1AsfpmHxrBzFRMuO0kH/uLZBBDkUNs0Xp+ogfPTQxgYo
52d1Tq3m0PsWSAp272vrsi+bt35qkfujXVvpnx3u4tMIqqWmN/rE6kvneiTaBmVE
eXhKnz9DLqNyiJP30jXT6fmX54LqNaDw0WFptII4ipD+0tLZ7pLE0huyx5iduzDz
ebeVAOxkLyBesrUoR4wdQiMve/N9fBWmm5dfxfmqJCVRC8zzn8a0lioK3PtLXP83
inGmwfBd13B8Z3n1IpIg6T0RwGjru3WuJLMBWzoKxKs2P/zIQ0Zcg4m3X9Ssf/xH
fusg9ON5AgMBAAECggEAE1uaEP/mVAOrq1qf2d4sMXfRIKG//eSC4A2rG+7RBDIE
XIbz/eV5jAvkT6Jx8qsM0lOuV5i0XDCxviiJSVJxNQpKdj0jtwaIX3X3fsG6fnEE
zeA/mTG51sqMG/vufQX+7HShCmGu9kHDcJHP30xUj4wnEmZKsjFxDD0OGH95gKYb
oC2IUQ8iOZJVnaK2Up4CHIz5mHwnfoDdcM1d/9yiKxhzivFYMb96hIUDVluml0lA
spNS0UqEh04ybAUf693X874zZN2nL9xE7gWXIn+9jaOv23HqaPxZBjHumaWOHOvn
N909pb78zaiK4N/eESEIS79RWAGeGZUieRWXO9TIgQKBgQDui6U8WfGQmYmLBejq
3GPKkgwgdw3F2niEeCJ4EeSmorqRCRIOtT3TCo4AJMiVg5Y5BTT/x1UcnyHoKxZi
b+pMc6k2KHH48dLoK873+PJW76VzUQ1RaNlz+kmy/f6WRHVoANwWK2UfhL1brTlN
lvhobL6FnaW62erm6Jd0O9/ggQKBgQDqqY6hCLQzEzTh5w0bkq6bGfHIwfHOXY/F
dDTvJE4MVGSTVRS6Xfu9lbSZ2bfol+w0kMPkD+9eUnZsSOtJaT1TZh7gyXgxvlYa
5NB6DjoF+AyPqkXcxRsDfLzseZlF1XFdnJWrKPaJgpw598x7d/8JyH6YnKpnmpFr
NCJtXLCG+QKBgAv8blALAO1QGa4nnN14N3dtQTi8Yq/HW3jkhG7eD0wkLxWsjAC7
MKETDbGKJ54Dn5+72D7l6Cvo/w4oZBaMIwy2XxE+lQN6Oyu5T8v78UlW/0w9DVtC
1nJSaDObOZiZVgDk0io3AfzEcbNSj+eLJ24v0J7sHfC2lGwH0dxgSc6BAoGBAJqM
v7ZJgD0fSjX6MYTWb48RYE/DhFlQ/66hIXfbJlgygOcUIwm3emRbo82sOdbDsDrS
mWGsKQ+rKfmZcPUxjcVOvcl4h2PjotwllTS+B/MEcmlwUIDdhDQgxGDOmWcH85ke
1ugam3zne7MmBBPRbTRpSw+CJy0C/QFpHb9/S3gpAoGAUgDjzwNrg7tXxexaqtY1
RF4DgWBcXfLj9Jl5nXRutdVsLeGq0OiV2x0wzdI0+BOz2yfuE32Gfeyvldo3yEB7
SG8Sg8MYlJnpP7XAi+AJm5Qbgi3CFrNFXvtYxDSgqu2rIzkoqOSddB3tzk8Pwk8k
79jnQnJDilR26CZT06cVYco=
-----END PRIVATE KEY-----
"""