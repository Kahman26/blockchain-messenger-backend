from marshmallow import Schema, fields, validate


class CreateUserSchema(Schema):
    username = fields.String(required=True, example="NoUsername", description="Уникальный ник пользователя")
    first_name = fields.String(required=True, example="Ivan", description="Имя пользователя")
    last_name = fields.String(required=True, example="Petrov", description="Фамилия пользователя")
    phone_number = fields.String(required=True, example="89222222222")
    email = fields.Email(required=True, example="ivan@example.com", description="Уникальный email")
    password = fields.String(required=True, validate=validate.Length(min=6), example="strongpassword", description="Пароль")
    birth_date = fields.Date(required=True, example="1990-01-01", description="Дата рождения в формате YYYY-MM-DD")
    is_admin = fields.Boolean(required=True, example=False, description="Признак администратора")


class UpdateUserSchema(Schema):
    username = fields.String(required=True, example="NoUsername")
    first_name = fields.String(required=True, example="Ivan")
    last_name = fields.String(required=True, example="Petrov")
    phone_number = fields.String(required=True, example="89222222222")
    email = fields.Email(required=True, example="ivan@example.com")
    password = fields.String(required=False, validate=validate.Length(min=6), example="newpass123")
    birth_date = fields.Date(required=True, example="1990-01-01")
    is_admin = fields.Boolean(required=True, example=False)


class UserResponseSchema(Schema):
    id = fields.Integer()
    first_name = fields.String()
    last_name = fields.String()
    login = fields.Email()
    birth_date = fields.Date()
    is_admin = fields.Boolean()
    is_blocked = fields.Boolean()
    updated_at = fields.DateTime()


class UserLastSeenSchema(Schema):
    user_id = fields.Int(required=True, example=2)
    username = fields.Str(required=True, example="Andrey")
    last_seen = fields.DateTime(required=True, example="2025-07-23T14:20:00")

