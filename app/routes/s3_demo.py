import uuid
import aioboto3
from aiohttp import web
from aiohttp_apispec import docs

from app.config import settings

routes = web.RouteTableDef()

@routes.post("/swagger/upload-image")
@docs(
    tags=["s3-demo"],
    summary="Загрузить картинку в Yandex Object Storage",
    description="multipart/form-data поле file (image/*). Загружает в бакет и возвращает presigned URL на 5 минут.",
    consumes=["multipart/form-data"],
    parameters=[
        {
            "in": "formData",
            "name": "file",
            "type": "file",
            "required": True,
            "description": "Image file to upload",
        }
    ],
    responses={
        200: {"description": "OK"},
        400: {"description": "Bad Request"},
        500: {"description": "Upload failed"},
    },
)
async def upload_image_to_s3(request: web.Request):
    reader = await request.multipart()
    part = await reader.next()

    if not part or part.name != "file":
        raise web.HTTPBadRequest(reason="Expected multipart field 'file'")

    filename = part.filename or "image.png"
    content_type = part.headers.get("Content-Type", "")

    if not content_type.startswith("image/"):
        raise web.HTTPBadRequest(reason="Only image/* content types are allowed")

    data = await part.read(decode=False)

    key = f"demo/{uuid.uuid4().hex}_{filename}".replace("/", "_").replace("\\", "_")

    session = aioboto3.Session()
    async with session.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT,          # https://storage.yandexcloud.net
        region_name=settings.S3_REGION,             # ru-central1
        aws_access_key_id=settings.S3_ACCESS_KEY_ID,
        aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
    ) as s3:
        await s3.put_object(
            Bucket=settings.S3_BUCKET,
            Key=key,
            Body=data,
            ContentType=content_type or "application/octet-stream",
        )

        presigned_url = await s3.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": settings.S3_BUCKET, "Key": key},
            ExpiresIn=300,
        )

    return web.json_response({
        "bucket": settings.S3_BUCKET,
        "key": key,
        "presigned_url": presigned_url,
        "expires_in": 300
    })
