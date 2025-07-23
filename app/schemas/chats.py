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

