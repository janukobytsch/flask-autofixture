import os
import shutil


# ==== Layout ====


class StorageLayout(object):
    """A strategy to layout a :class:`Fixture` in a :class:`Storage`."""

    @staticmethod
    def get_request_path(fixture):
        separator = '-'
        path = fixture.request_path.replace(os.sep, separator) \
            .strip(separator)
        return path


class RequestMethodLayout(StorageLayout):
    """This strategy lays out a :class:`Fixture` by its request method first.

    Example directory structure:

        /autofixture                        (the name of the extension)
            /app                            (the name of the app)
                /GET                        (the request method)
                    /api-posts              (the request path)
                        response.json
                /POST
                    /api-posts
                        request.json        (the request payload)
                        response.json       (the response data)
                        request_2.json
                        response_2.json
    """

    @staticmethod
    def path_components_for(fixture):
        request_path = StorageLayout.get_request_path(fixture)
        return [fixture.app_name, fixture.request_method,
                request_path, fixture.name]


class RouteLayout(StorageLayout):
    """This strategy lays out a :class:`Fixture` by its resource route first.

    Example directory structure:

        /autofixture                        (the name of the extension)
            /app                            (the name of the app)
                /api-posts                  (the request path)
                    /GET                    (the request method)
                        response.json
                    /POST
                        request.json        (the request payload)
                        response.json       (the response data)
                        request_2.json
                        response_2.json
    """

    @staticmethod
    def path_components_for(fixture):
        request_path = StorageLayout.get_request_path(fixture)
        return [fixture.app_name, request_path,
                fixture.request_method, fixture.name]


# ==== Storage ====


# A global map that keeps track of the persisted fixures and their versions
# This must be module-scoped to stay alive for the course of the test run
_dir_map = {}


class Storage(object):
    pass


class FileStorage(Storage):
    def __init__(self, layout_class, dirname, root_path):
        """The file storage object represents a strategy to persist the cached
        fixtures in a directory on the local file system.

        :param layout_class: the :class:`StorageLayout` for the fixture
                             directory
        :param dirname: the name for the fixture directory
        :param root_path: the parent of the fixture directory
        """
        self.layout = layout_class
        self.dirname = dirname
        self.root_path = root_path

    @property
    def fixture_directory(self):
        return os.path.join(self.root_path, self.dirname)

    def reset_directory(self):
        if os.path.exists(self.fixture_directory):
            shutil.rmtree(self.fixture_directory)

    def store_fixture(self, fixture):
        global _dir_map

        path_components = self.layout.path_components_for(fixture)

        # Handle multiple versions
        version = 0
        index = self._file_index(path_components)
        if index in _dir_map:
            version = _dir_map[index] + 1
        if version:
            path_components[-1] += '_{}'.format(version)
        _dir_map[index] = version

        # Append file type to last component
        path_components[-1] += '.{}'.format(fixture.type)

        # Flush data
        fn = os.path.join(self.fixture_directory, *path_components)
        os.makedirs(os.path.dirname(fn), exist_ok=True)
        with open(fn, 'w') as fd:
            fd.write(fixture.payload)

    def _file_index(self, path_components):
        """Generates a unique index for a given path for use as a key
        in the file map.

        :param path_components: the path within the fixture directory
        :return:
        """
        return str(hash(os.sep.join(path_components)))
