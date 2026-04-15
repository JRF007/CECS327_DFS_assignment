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

## What to replace later
Right now it uses `MockChord` so it runs immediately.
When you get your class Chord code connected, keep the `DFS` class and replace only the storage backend calls.
