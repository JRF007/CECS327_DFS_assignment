from dfs import DFS, ChordRing, ChordClient

ring = ChordRing(num_nodes=5)
chord = ChordClient(ring)
dfs = DFS(chord)
with open("big_sample.txt", "w", encoding="utf-8") as f:
    for i in range(1000):
        f.write(f"{i:04d},name{i}\n")
dfs.touch("records.txt")
dfs.append("records.txt", "sample.txt")
dfs.distributed_sort_file("records.txt", "sorted_records.txt")
print("Sorted file contents:")
print(dfs.read("sorted_records.txt").decode("utf-8"))
dfs.touch("big_records.txt")
dfs.append("big_records.txt", "big_sample.txt")
original = open("big_sample.txt", "rb").read()
rebuilt = dfs.read("big_records.txt")
print("Rebuild matches original:", original == rebuilt)
print("Big file metadata:", dfs.stat("big_records.txt"))
print("Big file page count:", dfs.stat("big_records.txt")["num_pages"])
print("Files:", dfs.ls())
print("Contents:\n", dfs.read("records.txt").decode("utf-8"))
print("Head 5:", dfs.head("records.txt", 5).decode())
print("Tail 5:", dfs.tail("records.txt", 5).decode())
dfs.delete_file("records.txt")
dfs.delete_file("sorted_records.txt")
dfs.delete_file("big_records.txt")
print("Final files:", dfs.ls())
print("After delete, files:", dfs.ls())
print("\nPaxos Logs:")
for i, node in enumerate(ring.nodes):
    print(f"Node {i} ({node.node_id}) log:")
    for msg_type, seq, op in node.paxos_log[:6]:
        key = op[0]
        print(f"   ({msg_type}, seq={seq}, key={key})")