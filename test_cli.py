from zipfile import Path
from cli import DirPath, InMemoryZF, parse_path
import pytest

@pytest.fixture
def setup_context():
    zf = InMemoryZF.from_zip("test.zip")
    root_path = Path(zf.zf)
    cur_path = DirPath("")

    cur_path_Path = lambda : root_path.joinpath(*[p for p in cur_path.n.split("/")]) if cur_path.n else root_path
    cd = lambda p: cur_path.cd(p, root_path)
    rev = lambda s: "".join([c for c in s[::-1]])
    ls = lambda s: '\n'.join([".", ".."] + [str(p.filename).replace('\\', '/').replace(f"{str(root_path.filename)}/{cur_path_Path().at}", "", 1) for p in cur_path_Path().iterdir()]) if not s else '\n'.join([".", ".."] + [str(p.filename).replace('\\', '/').replace(f"{str(root_path.filename)}/{cur_path_Path().at}", "", 1) for p in cur_path_Path().joinpath(*parse_path(s).split("/")).iterdir()])
    rm = lambda f: root_path.__init__(zf.delete_file(parse_path(cur_path.n + "/" + f)).zf)
    chown = lambda new_owner, file: root_path.__init__(zf.add_owner_metadata_to_file(new_owner, parse_path(cur_path.n + "/" + file)).zf)

    yield {'zf': zf, 'root_path': root_path, 'cur_path': cur_path, 'cd': cd, 'rev': rev, 'ls': ls, 'rm': rm, 'chown': chown}


def test_ls(setup_context):
    ctx = setup_context
    assert "main.c" in ctx['ls']("a")
    assert "main.py" in ctx['ls']("a/d")

def test_rm(setup_context):
    ctx = setup_context
    initial_files = ctx['ls']("a")
    ctx['rm']("a/main.c")
    after_rm_files = ctx['ls']("a")
    assert "main.c" in initial_files
    assert "main.c" not in after_rm_files

def test_chown(setup_context):
    """How am I supposed to test this, if zip archives don't even hold additional info to files, except comments?
    It runs.

    Args:
        setup_context (_type_): YES
    """
    ctx = setup_context
    ctx['chown']("vadim", "a/d/main.py")
    ctx['chown']("vadim", "a/main.c")

def test_rev(setup_context):
    ctx = setup_context
    assert ctx['rev']("hello") == "olleh"
    assert ctx['rev']("hello world") == "dlrow olleh"

def test_cd(setup_context):
    ctx = setup_context
    ctx['cd']("a")
    assert ctx['cur_path'].n == "a"
    ctx['cd']("../b/e")
    assert ctx['cur_path'].n == "b/e"

def test_parse_path():
    assert parse_path("a/b/../c/d/e/../../f/./g") == "a/c/f/g"
    assert parse_path("/a/d/b/../../e/././../f/./") == "a/f"