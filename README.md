# Distributed File System (DFS) over Chord

This project implements a simplified Distributed File System (DFS) built on top of a Chord-like Distributed Hash Table (DHT).

## Overview

The system extends a Chord-style key-value store into a file system by separating:

- **Metadata objects** (file structure)
- **Page objects** (file content chunks)

Each file is distributed across multiple nodes using deterministic hashing.

---

## Architecture

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

---

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

---

## Data Model

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