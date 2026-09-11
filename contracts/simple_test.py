# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

from genlayer import *


class SimpleTest(gl.Contract):
    value: u256

    def __init__(self):
        pass

    @gl.public.write
    def test_write(self) -> str:
        return "hello"

    @gl.public.view
    def test_view(self) -> str:
        return "world"
