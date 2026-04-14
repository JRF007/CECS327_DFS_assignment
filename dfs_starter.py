import hashlib
import json
from pathlib import Path

PAGE_SIZE = 4096


def sha1_hex(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


class MockChord:
    """Tiny stand-in for your real Chord layer."""

    def __init__(self):
        self.store = {}

    def put(self, key: str, value: bytes) -> None:
        self.store[key] = value

    def get(self, key: str):
        return self.store.get(key)

    def delete(self, key: str) -> None:
        self.store.pop(key, None)


class DFS:
    def __init__(self, chord):
        self.chord = chord
        self.directory_key = sha1_hex("dfs:directory")

    # ---------- key helpers ----------
    def metadata_key(self, filename: str) -> str:
        return sha1_hex(f"metadata:{filename}")

    def page_key(self, filename: str, page_no: int) -> str:
        return sha1_hex(f"{filename}:{page_no}")

    # ---------- directory helpers ----------
    def _get_directory(self):
        raw = self.chord.get(self.directory_key)
        if raw is None:
            return []
        return json.loads(raw.decode("utf-8"))

    def _put_directory(self, names):
        self.chord.put(self.directory_key, json.dumps(sorted(names)).encode("utf-8"))

    # ---------- metadata helpers ----------
    def _get_metadata(self, filename: str):
        raw = self.chord.get(self.metadata_key(filename))
        if raw is None:
            raise FileNotFoundError(filename)
        return json.loads(raw.decode("utf-8"))

    def _put_metadata(self, metadata: dict):
        self.chord.put(
            self.metadata_key(metadata["filename"]),
            json.dumps(metadata).encode("utf-8"),
        )

    # ---------- public DFS API ----------
    def touch(self, filename: str) -> None:
        try:
            self._get_metadata(filename)
            raise FileExistsError(filename)
        except FileNotFoundError:
            pass

        metadata = {
            "filename": filename,
            "size_bytes": 0,
            "num_pages": 0,
            "pages": [],
            "version": 1,
        }
        self._put_metadata(metadata)

        directory = self._get_directory()
        if filename not in directory:
            directory.append(filename)
            self._put_directory(directory)

    def append(self, filename: str, local_path: str, page_size: int = PAGE_SIZE) -> None:
        metadata = self._get_metadata(filename)
        data = Path(local_path).read_bytes()
        chunks = [data[i:i + page_size] for i in range(0, len(data), page_size)]

        start = metadata["num_pages"]
        for offset, chunk in enumerate(chunks):
            page_no = start + offset
            guid = self.page_key(filename, page_no)
            self.chord.put(guid, chunk)
            metadata["pages"].append(
                {"page_no": page_no, "guid": guid, "size_bytes": len(chunk)}
            )

        metadata["num_pages"] = len(metadata["pages"])
        metadata["size_bytes"] += len(data)
        metadata["version"] += 1
        self._put_metadata(metadata)

    def read(self, filename: str) -> bytes:
        metadata = self._get_metadata(filename)
        parts = []
        for page in sorted(metadata["pages"], key=lambda p: p["page_no"]):
            data = self.chord.get(page["guid"])
            if data is None:
                raise FileNotFoundError(f"Missing page {page['guid']}")
            parts.append(data)
        return b"".join(parts)

    def head(self, filename: str, n: int) -> bytes:
        return self.read(filename)[:n]

    def tail(self, filename: str, n: int) -> bytes:
        data = self.read(filename)
        return data[-n:] if n < len(data) else data

    def delete_file(self, filename: str) -> None:
        metadata = self._get_metadata(filename)
        for page in metadata["pages"]:
            self.chord.delete(page["guid"])
        self.chord.delete(self.metadata_key(filename))

        directory = self._get_directory()
        if filename in directory:
            directory.remove(filename)
            self._put_directory(directory)

    def ls(self):
        return self._get_directory()

    def stat(self, filename: str) -> dict:
        return self._get_metadata(filename)


if __name__ == "__main__":
    chord = MockChord()
    dfs = DFS(chord)

    sample = Path("sample.txt")
    if not sample.exists():
        sample.write_text("hello from dfs\nthis is a starter file\n")

    dfs.touch("demo.txt")
    dfs.append("demo.txt", "sample.txt")

    print("ls():", dfs.ls())
    print("stat():", dfs.stat("demo.txt"))
    print("read():")
    print(dfs.read("demo.txt").decode())
    print("head(5):", dfs.head("demo.txt", 5))
    print("tail(5):", dfs.tail("demo.txt", 5))
