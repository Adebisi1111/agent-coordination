# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

import json
from dataclasses import dataclass
import genlayer as gl
from genlayer import *

TreeMap = gl.storage.TreeMap


@allow_storage
@dataclass
class Greeting:
    message: str = "hello"


@gl.public.write
def set_message(new_msg: str) -> None:
    self.message = new_msg


@gl.public.view
def get_message() -> str:
    return self.message
