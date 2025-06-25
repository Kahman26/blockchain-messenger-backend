import asyncio
from app.utils import blockchain
from app.database.db import engine
from app.database.models import UserKeys
from sqlalchemy import select
import textwrap


async def generate_test_message_payload(sender_id: int, receiver_id: int, message: str, sender_priv_key: str) -> dict:
    async with engine.connect() as conn:
        # Получаем публичный ключ получателя из базы
        receiver_result = await conn.execute(select(UserKeys).where(UserKeys.c.user_id == receiver_id))
        receiver_key = receiver_result.fetchone()

        print("\n🔍 Публичный ключ получателя из базы:")
        print(receiver_key.public_key)

        if not receiver_key:
            raise ValueError(f"Публичный ключ пользователя receiver_id={receiver_id} не найден в базе.")

        # Шифруем сообщение публичным ключом получателя
        encrypted_message = blockchain.encrypt_message(message, receiver_key.public_key)

        # Подписываем сообщение приватным ключом (введённым вручную)
        signature = blockchain.sign_message(message, sender_priv_key)

        return {
            "receiver_id": receiver_id,
            "encrypted_message": encrypted_message,
            "signature": signature,
            "original_message": message
        }


if __name__ == "__main__":
    sender_id = 2
    receiver_id = 8
    message = "Привет, это тестовое сообщение!"

    sender_priv_key = """-----BEGIN PRIVATE KEY-----
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
-----END PRIVATE KEY-----"""

    try:
        result = asyncio.run(generate_test_message_payload(sender_id, receiver_id, message, sender_priv_key))
        print("\n📦 Готово! Вставь это в Swagger `/messages/send`:\n")
        print(result)
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")

# Шаблон для сваггера:
swagger = \
    {
  "receiver_id": 8,
  "encrypted_message": "gfD3DIOP/ypNs/Wce7hcFVU3YJsgi8KIypRbwaS8cfNdFANTlFbV6vyNaDfIk0x4MwIGTfobBEwwrt9sT/mQCO4yB2Sio6JqDRpBSV3Nzq7nQM48MpaHJhbC9pUwhh6zLH4ZM9KLDcRqd8cLABKURWCbVkfUkDDNJR/xbb7uDcvfGQeSzSQi3v5jjgPM2Ud35mJM/P5QtkEck/VkK0C5F14OVkc/p7C/elaJ2bagUq7Zxcxfkpaa26J31sBkvpx7Q1Z40O/VaFRLTRlWtzqkcBgPyrAQPQl9ZZD0bXfP+0fUymfGIV95s5gBQmHd4mBgGdT0rybxnWPA8gEH/0oQaQ==",
  "signature": "QXRyrbA1LQ3fOhepwMvQFiWuI/vh7inrlJtnfbogakuHZIpbcfp9C46pFsIPuK3y9t/riZq26EEMtVDew0HGhnZW+XLhcYkgjVmcSALso9vPtWU/P0ffykanh0/xQQ8r8d4onNjQ2hCFQuI/qkG2VISfHbPyy40PVD8jzsw7/IGOovXQlaqOCwVdyGb9pIiUAOhAng+JAfC8uWcjF6qz1DHqYPZVoUEcLlmZkquhRnXWs5bujux6TOOWlvBdQHrROZE779z8fyNUlGl1RLnHUuJ+8enujCUnvk853RtX4Rfnn8E9JX/fs84DGpHUvXnwELITN70eOB+4G8FFjA9f5A==",
  "original_message": "Привет, это тестовое сообщение!"
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