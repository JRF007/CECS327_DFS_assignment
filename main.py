from dfs_starter import DFS, MockChord

chord = MockChord()
dfs = DFS(chord)

# Create a tiny sample file if you do not have one yet.
with open("sample.txt", "w", encoding="utf-8") as f:
    f.write("0012,alice\n0042,bob\n0190,carol\n")

dfs.touch("records.txt")
dfs.append("records.txt", "sample.txt")

print("Files:", dfs.ls())
print("Metadata:", dfs.stat("records.txt"))
print("Contents:\n", dfs.read("records.txt").decode("utf-8"))
