"""
Command line tool for copying files from/to a container
"""

import argparse
import os
import re
import shutil

import docker


class NotSupportedStorageBackend(Exception):
    """
    Custom exception for handling unsupported storage backends
    """
    pass


class ContainerPathError(Exception):
    """
    Custom exception for handling wrong container path
    """
    pass


class Container(object):
    """
    Class for docker-cp magic...
    """
    def __init__(self, container, base_url='unix://var/run/docker.sock'):
        self.container = container
        self.client = docker.DockerClient(base_url)
        self.api = docker.APIClient(base_url)

    def get_storage_backend(self):
        """
        Get current storage backend
        """
        return self.client.info()['Driver']

    def cont_to_id(self):
        """
        Convert container name to an ID as IDs are preferred container
        identifiers
        """
        return self.client.containers.get(self.container).id

    def get_storage_vol(self, cont_id, store_backend):
        """
        Get the container storage volume path
        """
        if store_backend == 'devicemapper':
            dev_name = self.api.inspect_container(
                cont_id)['GraphDriver']['Data']['DeviceName']
            with open('/proc/mounts') as mounts:
                mounts = mounts.read()
                mnt_re = re.compile(r'{} (\S*)'.format(dev_name))
                mnt_path = re.search(mnt_re, mounts).group(1)
                cont_vol = os.path.join(mnt_path, 'rootfs')
                return cont_vol
        elif store_backend == 'overlay2':
            cont_vol = self.api.inspect_container(
                cont_id)['GraphDriver']['Data']['MergedDir']
            return cont_vol

        else:
            raise NotSupportedStorageBackend('Unsupported storage backend')


def copy_file(src, dest, buffer_size=None):
    """
    Copy files to/from
    """
    with open(src) as src_fo:
        with open(dest, 'w') as dest_fo:
            shutil.copyfileobj(src_fo, dest_fo, buffer_size)


def main():
    """
    Main tool entry-point
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--buffer-length', dest='buffer', type=int,
                        help='buffer size')
    parser.add_argument('src', help='source of a file')
    parser.add_argument('dest', help='destination of a file')
    args = parser.parse_args()
    buffer_size = args.buffer
    path_args = '{} {}'.format(args.src, args.dest)
    if path_args.count(':') != 1:
        raise ContainerPathError(
            'Please provide exactly one container as an endpoint')

    cont = re.search(r'\b(\S*):', path_args).group(1)

    container = Container(cont)
    backend_type = container.get_storage_backend()
    cont_id = container.cont_to_id()
    storage_vol = container.get_storage_vol(cont_id, backend_type)
    new_path = re.sub(cont+':', storage_vol+'/', path_args)
    new_path = os.path.normpath(new_path)
    src, dest = new_path.split()
    copy_file(src, dest, buffer_size=buffer_size)


if __name__ == "__main__":
    try:
        main()
    except ContainerPathError as exc:
        print(exc)
    except NotSupportedStorageBackend as exc:
        print(exc)
