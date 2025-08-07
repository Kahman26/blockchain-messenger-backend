from marshmallow import Schema, fields, validates_schema, ValidationError


class ChatCreateSchema(Schema):
    chat_type = fields.Str(required=True)  # 'private' | 'group' | 'channel'
    chat_name = fields.Str(missing=None)
    description = fields.Str(missing=None)
    other_user_id = fields.Int(missing=None)

    @validates_schema
    def validate_fields(self, data, **kwargs):
        if data["chat_type"] == "private":
            if not data.get("other_user_id"):
                raise ValidationError("Для приватного чата требуется поле other_user_id")
        else:
            if not data.get("chat_name"):
                raise ValidationError("Для группового или канального чата требуется поле chat_name")


class ChatResponseSchema(Schema):
    chat_id = fields.Int()
    chat_name = fields.Str()
    chat_type = fields.Str()
    creator_user_id = fields.Int()
    description = fields.Str()
    created_at = fields.DateTime()
    last_message_time = fields.DateTime(allow_none=True)


class ChatListSchema(Schema):
    chats = fields.List(fields.Nested(ChatResponseSchema))


class ChatAddMemberSchema(Schema):
    user_id = fields.Int(required=True)


class ChatMemberSchema(Schema):
    id = fields.Int(required=True)
    username = fields.Str(required=True)
    public_key = fields.Str(required=True)
    last_seen = fields.DateTime(required=True)


class ChatMembersResponseSchema(Schema):
    members = fields.List(fields.Nested(ChatMemberSchema))
