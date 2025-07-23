from marshmallow import Schema, fields


class SendMessageSchema(Schema):
    receiver_id = fields.Int(required=True, example=42, description="ID получателя")
    encrypted_message = fields.String(required=True, description="Зашифрованное сообщение (base64)")
    signature = fields.String(required=True, description="Подпись отправителя (base64)")
    original_message = fields.String(required=False, description="Оригинальное сообщение для проверки подписи (только на время тестов)")


class SendMessageResponseSchema(Schema):
    message = fields.String(example="Encrypted message recorded on blockchain")
    transaction_id = fields.Int(example=1234)


class InboxMessageSchema(Schema):
    from_user_id = fields.Int(required=True, example=2, description="ID отправителя")
    message = fields.String(required=True, description="Расшифрованное сообщение")
    timestamp = fields.String(required=True, example="2025-06-25T13:00:00", description="Время отправки сообщения")


class InboxResponseSchema(Schema):
    messages = fields.List(fields.Nested(InboxMessageSchema))


class EncryptedPerUserSchema(Schema):
    receiver_id = fields.Int(required=True)
    encrypted_message = fields.String(required=True)
    signature = fields.String(required=True)


class EncryptedBroadcastListSchema(Schema):
    __schema_type__ = "array"
    __schema_items__ = fields.Nested(EncryptedPerUserSchema)


class ChatMessageSchema(Schema):
    message_id = fields.Int(required=True, description="ID транзакции (сообщения)")
    from_user_id = fields.Int(required=True, description="ID отправителя")
    from_username = fields.Str(required=True, description="Имя пользователя отправителя")
    encrypted_data = fields.String(required=True, description="Зашифрованное сообщение (base64)")
    signature = fields.String(required=True, description="Подпись сообщения (base64)")
    timestamp = fields.String(required=True, description="Дата и время отправки")


class ChatMessageListSchema(Schema):
    messages = fields.List(fields.Nested(ChatMessageSchema), required=True)
