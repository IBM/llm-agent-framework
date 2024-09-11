# Standard
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, List, Optional
import abc
import asyncio
import hashlib
import json
import os

# Third Party
from sqlitedict import SqliteDict

# Local
from lm_agent.base.resource import BaseResource
from lm_agent.utils import lma_logger


@dataclass
class ModelResourceConfig(dict):
    model_backend: Optional[str] = None
    model_id_or_path: Optional[str] = None
    lm_cache: Optional[str] = None

    @classmethod
    def from_model_config(cls, model_cfg):
        return cls(
            model_backend=model_cfg.model_backend,
            model_id_or_path=model_cfg.model_id_or_path,
            lm_cache=model_cfg.lm_cache,
        )


@dataclass
class ModelResult(dict):
    generated_text: str
    input_token_count: int
    generated_token_count: int


MODEL_ID_OR_PATH = "model_id_or_path"


class BaseModel(BaseResource):
    """Class for LLMs"""

    MAX_CALLS = 100
    MAX_THREADS = 100

    def __init__(self, config: ModelResourceConfig):
        self._config = config
        self._rank = 0
        self.cache_hook = CacheHook(None)

        self._model_id_or_path: str = config.model_id_or_path

        assert (
            self._model_id_or_path is not None
        ), f"Must specify model for backend {config.model_backend}"

        self._base_kwargs = {
            "decoding_method": "greedy",
            "model_id_or_path": config.model_id_or_path,
        }

        self._semaphore = asyncio.Semaphore(self.MAX_CALLS)
        self._executor = ThreadPoolExecutor(self.MAX_THREADS)

    @property
    def semaphore(self):
        return self._semaphore

    @property
    def executor(self):
        return self._executor

    @property
    def rank(self):
        # used in the case of parallelism. Hardcoded to
        # ensure no errors arise using API models which do
        # not support multi-device parallelism nor expect it.
        return self._rank

    @property
    def config(self):
        return self._config

    @property
    def model_id_or_path(self):
        return self._model_id_or_path

    @property
    @abc.abstractmethod
    def eot_token_id(self):
        pass

    @property
    def prefix_token_id(self):
        # it is used as prefix for loglikelihood
        return self.eot_token_id

    @abc.abstractmethod
    async def loglikelihood(self, text: str, prefix: str = "", **kwargs) -> List:
        raise NotImplementedError

    @abc.abstractmethod
    async def generate(self, text: str, **kwargs) -> ModelResult:
        raise NotImplementedError

    def set_cache_hook(self, cache_hook) -> None:
        self.cache_hook = cache_hook


### SQLite-based caching of LM responses
def hash_args(attr, args, kwargs):
    dat = json.dumps([attr] + [args, kwargs])
    return hashlib.sha256(dat.encode("utf-8")).hexdigest()


class CacheHook:
    def __init__(self, cachinglm) -> None:
        if cachinglm is None:
            self.dbdict = None
            return

        self.dbdict: SqliteDict = cachinglm.dbdict

    def add_partial(self, attr, args, kwargs, res) -> None:
        if self.dbdict is None:
            return
        hsh = hash_args(attr, args, kwargs)
        self.dbdict[hsh] = res


class CachingLM:
    def __init__(self, lm: BaseModel, cache_db) -> Any:
        """LM wrapper that returns cached results if they exist, and uses the underlying LM if not.

        :param lm: LM
            Underlying LM
        :param cache_db: str
            Path to cache db
        """
        self.lm = lm
        self.cache_db = cache_db
        if os.path.dirname(cache_db):
            os.makedirs(os.path.dirname(cache_db), exist_ok=True)
        self.dbdict = SqliteDict(cache_db, autocommit=True)

        # add hook to lm
        lm.set_cache_hook(self.get_cache_hook())

        self.dbdict

    async def generate(self, *args: Any, **kwargs: Any) -> ModelResult:
        return await self._interface_handler("generate", *args, **kwargs)

    async def loglikelihood(self, *args: Any, **kwargs: Any):
        return await self._interface_handler("loglikelihood", *args, **kwargs)

    async def _interface_handler(self, attr: str, *args: Any, **kwargs: Any):
        # figure out which ones are cached and which ones are new
        lma_logger.debug(
            f"Using '{attr}' responses from cache '{self.cache_db}' where possible..."
        )
        res = None
        hsh = hash_args(attr, args, kwargs)
        if attr == "generate" and kwargs.get("decoding_method", None) == "sample":
            # when we are doing non-greedy generation, don't use the cache
            # (else every "randomly sampled" generation would be identical for repeats > 1).
            lma_logger.warning(
                f"Arguments to lm.generate_batch() '{kwargs}' include non-deterministic sampling. Caching will not be performed for such requests."
            )
            res = None
        elif hsh in self.dbdict:
            ob = self.dbdict[hsh]
            assert ob is not None
            res = ob

        if res is not None:
            lma_logger.debug(f"Cached request found!")
        else:
            res = await getattr(self.lm, attr)(*args, **kwargs)
            hsh = hash_args(attr, args, kwargs)
            self.dbdict[hsh] = res
            self.dbdict.commit()
        return res

    def __getattr__(self, attr):
        lm_attr = getattr(self.lm, attr)
        if attr not in ["generate", "loglikelihood"]:
            return lm_attr
        return getattr(self, attr)

    def get_cache_hook(self):
        return CacheHook(self)
