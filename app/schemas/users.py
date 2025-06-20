from marshmallow import Schema, fields, validate


class CreateUserSchema(Schema):
    first_name = fields.String(required=True, example="Ivan", description="Имя пользователя")
    last_name = fields.String(required=True, example="Petrov", description="Фамилия пользователя")
    login = fields.Email(required=True, example="ivan@example.com", description="Уникальный логин/email")
    password = fields.String(required=True, validate=validate.Length(min=6), example="strongpassword", description="Пароль")
    birth_date = fields.Date(required=True, example="1990-01-01", description="Дата рождения в формате YYYY-MM-DD")
    is_admin = fields.Boolean(required=True, example=False, description="Признак администратора")


class UpdateUserSchema(Schema):
    first_name = fields.String(required=True, example="Ivan")
    last_name = fields.String(required=True, example="Petrov")
    login = fields.Email(required=True, example="ivan@example.com")
    birth_date = fields.Date(required=True, example="1990-01-01")
    password = fields.String(required=False, validate=validate.Length(min=6), example="newpass123")
    is_admin = fields.Boolean(required=True, example=False)


class UserResponseSchema(Schema):
    id = fields.Integer()
    first_name = fields.String()
    last_name = fields.String()
    login = fields.Email()
    birth_date = fields.Date()
    is_admin = fields.Boolean()
    is_blocked = fields.Boolean()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()
