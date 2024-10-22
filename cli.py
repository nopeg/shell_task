from dataclasses import dataclass, field
from io import BytesIO
from zipfile import ZipFile, Path, ZipInfo
import argparse


@dataclass
class DirPath:
    n: str = ""

    def cd(self, path: str) -> None:
        self.n = parse_path(self.n + "/" + path)


@dataclass
class InMemoryZF:
    zf: ZipFile = field(init=False)

    def __init__(self, zf: ZipFile):
        self.zf = zf

    @classmethod
    def from_zip(cls, filename: str) -> 'InMemoryZF':
        with open(filename, 'rb') as zip_file:
            zf_buf = BytesIO(zip_file.read())
        zf_buf.seek(0)
        zf_buf.name = filename
        return cls(ZipFile(zf_buf))

    def delete_file(self, filepath: str) -> 'InMemoryZF':
        if self.zf is None:
            raise RuntimeError("Can't delete file, because no zip file was loaded. Load it using from_zip() method.")

        zf_buf = BytesIO()
        
        with ZipFile(zf_buf, 'w') as zf_operator:
            for item in self.zf.infolist():
                if item.filename != filepath:
                    file_contents = self.zf.read(item.filename)
                    zf_operator.writestr(item, file_contents)
        
        zf_buf.seek(0)
        zf_buf.name = self.zf.filename
        self.zf = ZipFile(zf_buf)
        return self
    
    def add_owner_metadata_to_file(self, owner: str, filepath: str) -> 'InMemoryZF':
        if self.zf is None:
            raise RuntimeError("Can't delete file, because no zip file was loaded. Load it using from_zip() method.")
        
        try:
            self.zf.getinfo(filepath)
        except KeyError:
            raise RuntimeError("File doesn't exist, can't change owner of non-existent file.")
        
        zf_buf = BytesIO()

        with ZipFile(zf_buf, 'w') as zf_operator:
            for item in self.zf.infolist():
                file_contents = self.zf.read(filepath)
                if item.filename == filepath:
                    info = ZipInfo(filepath)
                    info.comment = ("owner: " + owner).encode("utf-8")
                    zf_operator.writestr(info, file_contents)
                else:
                    zf_operator.writestr(item, file_contents)
        
        zf_buf.seek(0)
        zf_buf.name = self.zf.filename
        self.zf = ZipFile(zf_buf)

        return self


def parse_path(path: str) -> str:
    """calculates total path whithout .. from path with ..

    removes '/' for start and end

    Args:
        path (str): path to parse

    Returns:
        str: parsed paht string without .. or .
    
    Examples:
        >>> a = parse_path("/a/b../c/d/./e")
        >>> print(a)
        /a/c/d/e/
    """
    result = []
    parts = path.split("/")
    for part in parts:
        if part:
            if part == ".":
                continue
            elif part == "..":
                if result:
                    result.pop()
            else:
                result.append(part)
    return "/".join(result)


def main():
    parser = argparse.ArgumentParser(description='Shell emulator.')
    parser.add_argument('machine_name', type=str, help='Machine name')
    parser.add_argument('zip_file_path', type=str, help='Path to the zip file')
    parser.add_argument('script_file_path', type=str, help='Path to the script file')

    args = parser.parse_args()

    print(args.zip_file_path)

    zf = InMemoryZF.from_zip(args.zip_file_path)
    root_path = Path(zf.zf)
    cur_path = DirPath("")

    cur_path_Path = lambda : root_path.joinpath(*[p for p in cur_path.n.split("/")]) if cur_path.n else root_path
    cd = lambda p: cur_path.cd(p)
    rev = lambda s: "".join([c for c in s[::-1]])
    ls = lambda s: '\n'.join([".", ".."] + [str(p.filename).replace('\\', '/').replace(f"{str(root_path.filename)}/{cur_path_Path().at}", "", 1) for p in cur_path_Path().iterdir()]) if not s else '\n'.join([".", ".."] + [str(p.filename).replace('\\', '/').replace(f"{str(root_path.filename)}/{cur_path_Path().at}", "", 1) for p in cur_path_Path().joinpath(*parse_path(s).split("/")).iterdir()])
    rm = lambda f: root_path.__init__(zf.delete_file(parse_path(cur_path.n + "/" + f)).zf)
    chown = lambda new_owner, file: root_path.__init__(zf.add_owner_metadata_to_file(new_owner, parse_path(cur_path.n + "/" + file)).zf)

    if args.script_file_path:
        with open(args.script_file_path, "r", encoding="utf-8") as script:
            for line in script.readlines():
                command = line.replace('\n', '').split()
                print('\033[92m' + f"{args.machine_name} {cur_path.n}/ >" + '\033[0m' + f" {' '.join(command)}")
                match command[0]:
                    case "exit":
                        break
                    case "cd":
                        cd(command[1])
                    case "ls":
                        arg = command[1] if len(command) > 1 else ""
                        print(ls(arg))
                    case "chown":
                        chown(command[1], command[2])
                    case "rm":
                        rm(command[1])
                    case "rev":
                        print(rev(" ".join(command[1:])))
                    case _:
                        print(f"{command[0]}: command not found")


if __name__ == "__main__":
    main()