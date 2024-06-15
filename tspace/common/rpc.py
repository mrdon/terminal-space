import functools
import inspect
import json
from asyncio import Future
from types import SimpleNamespace
from typing import Awaitable, Any, Optional, Type, TypeVar
from typing import Callable

from pjrpc import AbstractRequest, AbstractResponse, Request
from pjrpc.client import AbstractAsyncClient
from pjrpc.server import AsyncDispatcher, MethodRegistry, Method
from pydantic import BaseModel
from pjrpc.server.validators import pydantic as validators

from tspace.client.logging import log

T = TypeVar('T')


class ClientAndServer(AbstractAsyncClient):

    async def _request(self, request_text: str, is_notification: bool = False, **kwargs: Any) -> Optional[str]:
        raise NotImplemented

    def __init__(self, sender: Callable[[str], Awaitable[None]]) -> None:
        super().__init__()
        self.sender = sender
        self.futures: dict[str, Future[str]] = {}
        self.dispatcher = AsyncDispatcher()

    def build_client(self, cls: type[T]) -> T:
        class Proxy:
            """
            Proxy object. Provides syntactic sugar to make method call using dot notation.

            :param client: JSON-RPC client instance
            """

            def __init__(self, client: 'BaseAbstractClient'):
                self._client = client

            def __getattr__(self, attr: str) -> Callable[..., Any]:
                notify = attr.startswith('on_')
                if notify:
                    log.info("notify call")
                    return functools.partial(self._client.notify, attr)

                async def wrapped_call(*args, **kwargs):
                    result = await self._client.call(attr, *args, **kwargs)
                    orig_method = getattr(cls, attr)
                    return_type = orig_method.__annotations__.get('return')
                    if getattr(return_type, "parse_obj"):
                        return return_type.parse_obj(result)
                    return result

                return wrapped_call

        return Proxy(self)

    def register_methods(self, obj: object) -> None:
        registry = MethodRegistry()
        validator = validators.PydanticValidator()
        for name, fn in {
            name: fn
            for name, fn in inspect.getmembers(obj, inspect.ismethod)
            if not name.startswith("_")
        }.items():

            async def call(local_fn, *args: Any, **kwargs: Any) -> Any:
                resp = await local_fn(*args, **kwargs)
                if isinstance(resp, BaseModel):
                    resp = resp.model_dump()
                return resp

            registry.add_methods(Method(validator.validate(functools.wraps(fn)(functools.partial(call, fn))),
                                        name=name))
        self.dispatcher.add_methods(registry)

    def unregister_methods(self, target: object) -> None:
        reg = self.dispatcher.registry
        # todo: not sure if I need to do anything as the new will just overwrite the old?

    @AbstractAsyncClient.retried
    @AbstractAsyncClient.traced
    async def _send(
            self,
            request: AbstractRequest,
            response_class: Type[AbstractResponse],
            validator: Callable[..., None],
            _trace_ctx: SimpleNamespace = SimpleNamespace(),
            **kwargs: Any,
    ) -> Optional[AbstractResponse]:
        # kwargs = {**self._request_args, **kwargs}
        assert isinstance(request, Request)

        match request.params:
            case list():
                converted = [c.model_dump() if isinstance(c, BaseModel) else c for c in request.params]
            case tuple():
                converted = (c.model_dump() if isinstance(c, BaseModel) else c for c in request.params)
            case dict():
                converted = {key: c.model_dump() if isinstance(c, BaseModel) else c for key, c in request.params.items()}
            case _:
                raise NotImplementedError(f"unsupported request type: {type(request.params)}")

        serialized_request = Request(
            method=request.method,
            params=converted,
            id=request.id,
        )
        log.info(f"Calling {request.method}")
        request_text = self.json_dumper(serialized_request, cls=self.json_encoder)

        try:
            log.info("calling")

            await self.sender(request_text)
        finally:
            log.info("Called")

        if not request.is_notification:
            log.info("is not notif")
            assert isinstance(request, Request)
            future = self.futures[request.id] = Future[str]()
            log.info("waiting on future")
            await future
            log.info("future done")
            response_text = future.result()
            if isinstance(response_text, str):
                response_text = self.json_loader(response_text, cls=self.json_decoder)

            response = response_class.from_json(response_text, error_cls=self.error_cls)
            validator(request, response)

        else:
            response = None

        return response

    async def on_incoming(self, text: str) -> None:
        log.info(f"incoming: {text}")
        if not "jsonrpc" in text:
            return

        # fixme: stop loading twice
        data = json.loads(text)
        if data.get("jsonrpc") == "2.0":
            if "result" in data:
                log.info(f"got result: {text}")
                fut = self.futures.get(data["id"])
                if fut:
                    fut.set_result(data)
            else:
                log.info(f"Got something else: {text}")
                try:
                    resp = await self.dispatcher.dispatch(text)
                    if resp:
                        await self.sender(resp)
                except Exception as e:
                    log.error(f"error: {e}", exc_info=True)
                    raise


