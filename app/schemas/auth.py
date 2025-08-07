from marshmallow import Schema, fields, validate


class RegisterSchema(Schema):
    email = fields.Email(
        required=True,
        example="user@example.com",
        description="Email пользователя"
    )
    password = fields.String(
        required=True,
        validate=validate.Length(min=6),
        example="securepassword123",
        description="Пароль (минимум 6 символов)"
    )
    username = fields.String(required=True)
    phone_number = fields.String(required=True)
    public_key = fields.String(required=True)


class ConfirmEmailSchema(Schema):
    email = fields.Email(required=True, example="user@example.com")
    code = fields.String(
        required=True,
        validate=validate.Regexp(r"^\d{6}$"),
        example="123456",
        description="Код подтверждения с почты"
    )


class LoginSchema(Schema):
    email = fields.Email(
        required=True,
        example="paa-gta@mail.ru",
        description="Email, зарегистрированный в системе"
    )
    password = fields.String(
        required=True,
        example="123456",
        description="Пароль, указанный при регистрации"
    )
    device_id = fields.String(
        required=True,
    )


class TokenResponse(Schema):
    access_token = fields.String(
        required=True,
        description="JWT access токен, используемый для авторизации"
    )
    refresh_token = fields.String(required=True)


class RefreshTokenSchema(Schema):
    refresh_token = fields.String(required=True)


class EmailSchema(Schema):
    email = fields.Email(
        required=True,
        example="user@example.com",
        description="Email пользователя, на который будет отправлен код подтверждения"
    )


class ResetPasswordSchema(Schema):
    email = fields.Email(
        required=True,
        example="user@example.com",
        description="Email, на который был выслан код подтверждения"
    )
    code = fields.String(
        required=True,
        validate=validate.Regexp(r"^\d{6}$"),
        example="123456",
        description="Код подтверждения, полученный по почте"
    )
    new_password = fields.String(
        required=True,
        validate=validate.Length(min=6),
        example="newSecurePass123",
        description="Новый пароль (минимум 6 символов)"
    )

