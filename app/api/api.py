import os
import uuid
import boto3
from botocore.exceptions import ClientError
from flask import request, send_from_directory
from flask_security import (
    login_required,
)
from werkzeug.utils import secure_filename
from app.api import bp
from app.utils import OK_RESPONSE, get_request_arg
from config import Config


@bp.route("/api/info", methods=["GET"])
@login_required
def info():
    return {"app_version": Config.APP_VERSION}


@bp.route("/api/upload", methods=["POST"])
def upload():
    object_names = []
    for file in request.files.getlist("file"):
        f = file
        f.save(os.path.join(Config.UPLOAD_FOLDER, secure_filename(f.filename)))
        object_name = f"{uuid.uuid4().hex}/{secure_filename(f.filename)}"
        s3_client = boto3.client(
            "s3",
            aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=Config.AWS_ACCESS_KEY_SECRET,
        )
        try:
            s3_client.upload_file(
                os.path.join(Config.UPLOAD_FOLDER, secure_filename(f.filename)),
                Config.AWS_UPLOADS_BUCKET,
                object_name,
            )
        except ClientError as e:
            return {"message": "Failed to upload!"}, 500
        object_names.append({"filename": object_name})
    return {"files": object_names}, 200


@bp.route("/api/download", methods=["GET"])
def download():
    bucket_path = get_request_arg(request, "file_name")
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=Config.AWS_ACCESS_KEY_SECRET,
    )
    with open(
        os.path.join(Config.DOWNLOAD_FOLDER, os.path.basename(bucket_path)), "wb"
    ) as data:
        s3_client.download_fileobj(Config.AWS_UPLOADS_BUCKET, bucket_path, data)
    return send_from_directory(Config.DOWNLOAD_FOLDER, os.path.basename(bucket_path))
