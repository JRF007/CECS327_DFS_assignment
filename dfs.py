import hashlib
import json
from pathlib import Path

PAGE_SIZE = 1024


def sha1_hex(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()

class Node:
    def __init__(self, node_id):
        self.node_id = node_id
        self.store = {}
        self.successor = None
        self.predecessor = None
        self.paxos_log = []

class ChordRing:
    def __init__(self, num_nodes=5):
        max_id = 2**160 - 1
        step = max_id // num_nodes
        self.nodes = []
        for i in range(num_nodes):
            node_id = (i + 1) * step
            self.nodes.append(Node(node_id))
        self.nodes.sort(key=lambda n: n.node_id)

        for i, node in enumerate(self.nodes):
            node.successor = self.nodes[(i + 1) % len(self.nodes)]
            node.predecessor = self.nodes[(i - 1) % len(self.nodes)]

    def locate_successor(self, key: str):
        key_int = int(key, 16)

        for node in self.nodes:
            if key_int <= node.node_id:
                return node

        return self.nodes[0]

class ChordClient:
    def __init__(self, ring):
        self.ring = ring

    def put(self, key, value):
        node = self.ring.locate_successor(key)
        node.store[key] = value

    def get(self, key):
        node = self.ring.locate_successor(key)
        return node.store.get(key)

    def delete(self, key):
        node = self.ring.locate_successor(key)
        node.store.pop(key, None)

class DFS:
    def __init__(self, chord):
        self.chord = chord
        self.directory_key = sha1_hex("dfs:directory")
        self.sequence_num = 0

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
        metadata_bytes = json.dumps(metadata).encode("utf-8")
        metadata_guid = self.metadata_key(filename)
        self.paxos_propose(metadata_guid, metadata_bytes)
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

            #self.chord.put(guid, chunk)
            #self.put_replicated(guid, chunk)
            self.paxos_propose(guid, chunk)

            metadata["pages"].append(
                {"page_no": page_no, "guid": guid, "size_bytes": len(chunk)}
            )
        metadata["num_pages"] = len(metadata["pages"])
        metadata["size_bytes"] += len(data)
        metadata["version"] += 1
        metadata_bytes = json.dumps(metadata).encode("utf-8")
        metadata_guid = self.metadata_key(filename)
        self.paxos_propose(metadata_guid, metadata_bytes)

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




    def distributed_sort_file(self, filename: str, sorted_filename: str):
        data = self.read(filename).decode("utf-8")
        lines = data.split("\n")
        records = []
        for line in lines:
            if line.strip() != "":
                parts = line.split(",")
                key = parts[0]
                value = parts[1]
                records.append((key, value))
        node_records = {}
        for node in self.chord.ring.nodes:
            node_records[node] = []
        for key, value in records:
            node = self.chord.ring.locate_successor(sha1_hex(key))
            node_records[node].append((key, value))
        for node in node_records:
            node_records[node].sort(key=lambda x : x[0])
        all_records = []
        for node in node_records:
            all_records.extend(node_records[node])
        all_records.sort(key=lambda x: x[0])
        sorted_lines = []
        for key, value in all_records:
            sorted_lines.append(key + "," + value)
        sorted_text = "\n".join(sorted_lines) + "\n"
        try:
            self.touch(sorted_filename)
        except FileExistsError:
            self.delete_file(sorted_filename)
            self.touch(sorted_filename)
        temp_file = "temp_sorted.txt"
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(sorted_text)
        self.append(sorted_filename, temp_file)


    def put_replicated(self, key, value, num_replicas = 3):
        node = self.chord.ring.locate_successor(key)

        for i in range(num_replicas):
            node.store[key] = value
            node = node.successor

    def accept(self, node, o, t):
        node.paxos_log.append(("Accept", t, o))
        return True

    def learn(self, node, o, t):
        node.paxos_log.append(("Learn", t, o))
        return True
    
    def paxos_propose(self, key, value):
        nodes = self.get_replica_nodes(key, 3)
        total = len(nodes)
        self.sequence_num += 1
        seq = self.sequence_num
        o = (key, value)
        t = seq
        accepts = 0
        for node in nodes:
            if self.accept(node, o, t):
                accepts += 1

        if accepts >= (total // 2 + 1):
            learns = 0

            for node in nodes:
                if self.learn(node, o, t):
                    learns += 1

            if learns >= (total // 2 + 1):
                self.put_replicated(key, value)
                print(f"Paxos commit ({seq}): {key}")
            else:
                print("Learns Failed")

        else:
            print("Accepts Failed")


    def get_replica_nodes(self, key, num_replicas=3):
        start = self.chord.ring.locate_successor(key)
        replicas = []
        node = start
        for _ in range(num_replicas):
            replicas.append(node)
            node = node.successor
        return replicas

    def put_replicated(self, key, value, num_replicas=3):
        replicas = self.get_replica_nodes(key, num_replicas)
        for node in replicas:
            node.store[key] = value
