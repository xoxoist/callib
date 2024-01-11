# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

import requests
from enum import Enum, auto
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

class Method(Enum):
    POST = auto()
    GET = auto()
    PATCH = auto()
    UPDATE = auto()
    DELETE = auto()

    def __str__(self):
        return self.name

class Call:
    def __init__(self, base_url: str, **kwargs):
        if not all(key in kwargs for key in ["connection", "size", "retry"]):
            raise Exception("connection, size and retry should be inside keyword argument")
        self.__base_url = base_url
        self.__connection = kwargs["connection"]
        self.__size = kwargs["size"]
        self.__retry = kwargs["retry"]
        adapter_config = (self.__connection, self.__size, self.__retry)
        self.adapter = self.__create_http_adapter(*adapter_config)
        self.session = requests.Session()
        self.session.mount("http://", self.adapter)
        self.session.mount("https://", self.adapter)

    def __create_http_adapter(self, connection: int, size: int, retry: int) -> HTTPAdapter:
        return HTTPAdapter(
            pool_connections=connection,
            pool_maxsize=size,
            max_retries=Retry(
                total=retry,
                backoff_factor=0.5,
            ))

    def add_header(self, header: dict):
        self.session.headers.update(header)

    def call(self, method: Method, path: str):
        complete_url = f"{self.__base_url}{path}" if self.__base_url else path
        return self.session.request(str(method), complete_url)


def main():
    cl_jsonplaceholder = Call("https://jsonplaceholder.typicode.com/", connection=5, size=10, retry=5)
    cl_jsonplaceholder.add_header({"Content-Type": "application/json"})
    result = cl_jsonplaceholder.call(Method.GET, "posts")
    print(result.status_code)
    print(result.elapsed)
    print(result.headers)
    print(result.reason)
    print(result.text)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
