# DFS

This is the smallest practical starter for your part of the project.

## Files
- `dfs_starter.py` - almost everything: key hashing, mock Chord, DFS API
- `main.py` - tiny demo runner
- `README.md` - setup notes

## What it supports
- `touch(filename)`
- `append(filename, local_path)`
- `read(filename)`
- `head(filename, n)`
- `tail(filename, n)`
- `delete_file(filename)`
- `ls()`
- `stat(filename)`

## Run it
```bash
python3 main.py
```

## What this implementation demonstrates
- File metadata stored in the DHT
- Page-based file storage
- Deterministic key mapping
- Multi-page file reconstruction
- Correctness validation (rebuild matches original)
