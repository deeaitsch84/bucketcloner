import argparse
import os
import sys
import tarfile
from typing import List, Optional

from bitbucket import clone_bitbucket, list_workspaces
from s3 import upload as upload_s3


def compress(workspace: str, repositories: list[str]) -> None:
    """
    Compresses the repositories in the workspace.
    :param workspace:
    :param repositories:
    :return:
    """
    print(f'Compressing repositories in {workspace}')
    directories = [d for d in os.listdir(workspace) if os.path.isdir(os.path.join(workspace, d)) and (d in repositories or not repositories)]
    # For each directory, create a tar file
    for directory in directories:
        print(f'Compressing {directory}')
        with tarfile.open(f"{workspace}/{directory}.tar.gz", "w:gz") as tar:
            tar.add(os.path.join(workspace, directory), arcname=os.path.basename(directory))


def upload(workspace, repositories: list[str], access_key_id: str,
           secret_key: str, region: str, endpoint: str, bucket: str) -> None:
    """
    Uploads the repositories to the cloud provider.
    :param repositories:
    :param bucket:
    :param region:
    :param endpoint:
    :param workspace:
    :param access_key_id:
    :param secret_key:
    :return:
    """
    print(f'Uploading compressed repositories to {endpoint}')

    if dir:
        # list all tar files in the workspace and prefix with directory
        payload = [f'{workspace}/{f}' for f in os.listdir(workspace) if
                   f.endswith('.tar.gz') and (f.split('.')[0] in repositories or not repositories)]

        for p in payload:
            if upload_s3(access_key_id=access_key_id,
                         secret_key=secret_key,
                         region=region,
                         endpoint=endpoint,
                         file_name=p,
                         bucket=bucket):
                os.remove(p)


def main(args: List[str]):
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--user', help='Username', required=True)
    parser.add_argument('-p', '--password', help='App password', required=True)
    parser.add_argument('-w', '--workspace', help='Workspace name(s), separated by comma')
    parser.add_argument('-r', '--repository', help='Repository name(s), separated by comma')
    parser.add_argument('-c', '--compress', help='Compress fetched repositories', action='store_false')
    parser.add_argument('--upload', help='Upload the compressed repositories', action='store_true')
    parser.add_argument('--s3-region', help='S3 region', required=False)
    parser.add_argument('--s3-endpoint', help='S3 endpoint', required=False)
    parser.add_argument('--s3-access-key-id', help='S3 access key id', required=False)
    parser.add_argument('--s3-secret-key', help='S3 secret key', required=False)
    parser.add_argument('--s3-bucket', help='S3 bucket name', required=False)
    parser.add_argument('command', help='Command', choices=['clone', 'workspace'])

    namespace = parser.parse_args(args)

    if namespace.command == 'clone':

        if namespace.repository:
            repositories = namespace.repository.split(',')
        else:
            repositories = []

        clone_bitbucket(namespace.user, namespace.password, namespace.workspace, repositories)

        if namespace.compress:
            compress(namespace.workspace, repositories)

        if namespace.upload:

            if not namespace.s3_access_key_id:
                parser.error('The s3-access-key-id argument is required for the upload command')

            if not namespace.s3_secret_key:
                parser.error('The s3-secret-key argument is required for the upload command')

            if not namespace.s3_region:
                parser.error('The s3-region argument is required for the upload command')

            if not namespace.s3_endpoint:
                parser.error('The s3-endpoint argument is required for the upload command')

            if not namespace.s3_bucket:
                parser.error('The s3-bucket argument is required for the upload command')

            print('Uploading the compressed repositories')
            upload(namespace.workspace,
                   repositories,
                   namespace.s3_access_key_id,
                   namespace.s3_secret_key,
                   namespace.s3_region,
                   namespace.s3_endpoint,
                   namespace.s3_bucket)

    elif namespace.command == 'workspace':
        workspaces = list_workspaces(namespace.user, namespace.password)
        for w in workspaces:
            print(f'{w["name"]} ({w["slug"]}) - {w["url"]}')


def entry_point():
    main(sys.argv[1:])


if __name__ == '__main__':
    entry_point()
