import logging
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
import os


def upload(access_key_id: str, secret_key: str, region: str, endpoint: str, file_name: str, bucket: str,
           object_name=None):
    """Upload a file to an S3 bucket

    :param access_key_id:
    :param secret_key:
    :param region:
    :param endpoint:
    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    s3 = boto3.client('s3', aws_access_key_id=access_key_id,
                      aws_secret_access_key=secret_key, region_name=region,
                      endpoint_url=endpoint)

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = os.path.basename(file_name)

    print(f'Uploading {file_name} to {bucket}/{object_name}')

    try:
        response = s3.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False

    return True
