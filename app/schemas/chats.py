from marshmallow import Schema, fields


class ChatCreateSchema(Schema):
    chat_name = fields.Str(required=True)
    chat_type = fields.Str(required=True)  # 'private' | 'group' | 'channel'
    description = fields.Str(missing=None)


class ChatResponseSchema(Schema):
    chat_id = fields.Int()
    chat_name = fields.Str()
    chat_type = fields.Str()
    creator_user_id = fields.Int()
    description = fields.Str()
    created_at = fields.DateTime()


class ChatListSchema(Schema):
    chats = fields.List(fields.Nested(ChatResponseSchema))


class ChatAddMemberSchema(Schema):
    user_id = fields.Int(required=True)

