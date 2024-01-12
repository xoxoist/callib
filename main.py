# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

import json
import requests
from typing import Type, List
from enum import Enum, auto
from pydantic import BaseModel
from pydantic import ValidationError
from requests import Response
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


class Condition(Enum):
    Malformed = auto()
    Unregister = auto()
    Timeout = auto()
    Invalid = auto()

    def __str__(self):
        return self.name


class Perform:
    def __init__(self, name: str, path: str, method: Method, response: Type[BaseModel]):
        self.response_model = response
        self.path = path
        self.method = method
        self.name = name


class PerformResult:
    def __init__(self, response: Response, perform: Perform):
        casted_result = perform.response_model(**json.loads(response.text))
        self.data = casted_result.model_dump()
        self.http_code = response.status_code
        self.headers = response.headers


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
        self.apis: List[Perform] = []

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

    def add_api(self, perform: Perform):
        self.apis.append(perform)

    def execute(self, name: str, request: BaseModel) -> PerformResult | Condition:
        try:
            selected_api = [api for api in self.apis if api.name == name][0]
            path = selected_api.path
            method = str(selected_api.method)
            complete_url = f"{self.__base_url}{path}" if self.__base_url else path
            request_dumped = request.model_dump()
            header_data = request_dumped["headers"]
            if header_data:
                self.session.headers.update(header_data)
                del request_dumped["headers"]
            result = self.session.request(method, complete_url, json=request_dumped)
            return PerformResult(result, selected_api)
        except IndexError:
            return Condition.Unregister
        except TimeoutError:
            return Condition.Timeout
        except json.JSONDecodeError:
            return Condition.Malformed
        except ValidationError:
            return Condition.Invalid


class CreatePostReq(BaseModel):
    title: str | None
    body: str | None
    userId: int | None
    headers: dict = {}


class CreatePostRes(BaseModel):
    id: int | None = None
    title: str | None = None
    body: str | None = None
    userId: int | None = None


def main():
    # api initialization
    base_url = "https://1290912671264cc1a9235d4525eef0b1.api.mockbin.io/"
    cl_jsonplaceholder = Call(base_url, connection=5, size=10, retry=5)
    cl_jsonplaceholder.add_header({"Content-Type": "application/json"})
    cl_jsonplaceholder.add_api(Perform("create_post", "posts", Method.POST, CreatePostRes))

    # api execution
    create_post_request = CreatePostReq(
        headers={"User-Agent": "Call-Lib-Test/1.0"},
        title="Foo2",
        body="Bar2",
        userId=2,
    )

    # checking condition
    create_post_res = cl_jsonplaceholder.execute("create_post", create_post_request)
    if type(create_post_res) is not PerformResult:
        print("error while calling api", create_post_res)
    if type(create_post_res) is PerformResult:
        created_post = CreatePostRes(**create_post_res.data)
        print("id", created_post.id)
        print("title", created_post.title)
        print("body", created_post.body)
        print("userId", created_post.userId)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
