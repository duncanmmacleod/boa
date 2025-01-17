import pathlib
from subprocess import check_call
import pytest
import sys


@pytest.mark.skipif(
    sys.platform.startswith("win"), reason="TODO new-style recipes noarch on Windows"
)
def test_build_recipes():
    recipes_dir = pathlib.Path(__file__).parent / "recipes-v2"

    recipes = [str(x) for x in recipes_dir.iterdir() if x.is_dir()]

    for recipe in recipes:
        check_call(["boa", "build", recipe])


def test_build_notest():
    recipes_dir = pathlib.Path(__file__).parent / "recipes-v2"

    recipes = [str(x) for x in recipes_dir.iterdir() if x.is_dir()]
    recipe = recipes[0]

    check_call(["boa", "build", recipe, "--no-test"])
