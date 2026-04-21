# Distributed File System (DFS) over Chord

This project implements a simplified Distributed File System (DFS) built on top of a Chord-like Distributed Hash Table (DHT).

## Overview
The system extends a Chord-style key-value store into a file system by separating:
Each file is distributed across multiple nodes using deterministic hashing.

## Run
```bash
python3 main.py
```

### Chord Layer (Simplified)
- A ring of 5 nodes is created
- Each node has:
  - `node_id`
  - local key-value storage
  - successor and predecessor
- Keys are routed to the responsible node using:
  - `locate_successor(key)`

### DFS Layer
- Metadata and pages are stored in the DHT
- Files are split into fixed-size pages
- Pages are distributed across nodes using hashed keys

## DFS Operations
The following API is implemented:
- `touch(filename)` → create empty file
- `append(filename, local_path)` → add file contents as pages
- `read(filename)` → reconstruct full file
- `head(filename, n)` → first `n` bytes
- `tail(filename, n)` → last `n` bytes
- `delete_file(filename)` → remove file and pages
- `ls()` → list files
- `stat(filename)` → return metadata
- `distributed_sort_file(input_filename, output_filename)` → sorts records of the form `key,value` and stores the sorted result as a new DFS file

## Paxos Replication
This project includes a simplified Paxos-style replication layer for DFS updates. A leader proposes an operation with a sequence number. The replicas receive ACCEPT messages, and then LEARN messages. Once a majority confirms the operation, the update is committed and applied in the same order across replicas. In our implementation, replicated writes are used during file page storage, and Paxos commit messages are printed during execution for debugging.

## Distributed Sorting
The system supports distributed sorting of files containing records in the format (key,value).
The sorting workflow is:
1. Read the input file from the DFS
2. Parse records into `(key, value)` pairs
3. Route each record to a responsible node
4. Sort records locally at each node
5. Combine the results into a globally sorted output file
6. Store the result as a new DFS file

### Where
In `dfs.py`, inside `append()`:
Right now pages go through:
```python
self.paxos_propose(guid, chunk)
```

### Metadata Object
```json
{
  "filename": "example.txt",
  "size_bytes": 12890,
  "num_pages": 13,
  "pages": [
    {"page_no": 0, "guid": "...", "size_bytes": 1024}
  ],
  "version": 2
}
```