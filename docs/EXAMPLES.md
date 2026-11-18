# pycliphist — Examples

Recipes for everyday use. All commands assume `pycliphist` is installed
(`pipx install pycliphist`) or run via `python -m pycliphist` with
`PYTHONPATH=src`.

## 1. Capture from the clipboard in the background

```console
$ pycliphist start --interval 0.5 --max-entries 1000
# ... copy things as you work ...
^C
Captured 12 clip(s).
```

## 2. Add clips from scripts and pipelines

`add` reads standard input when no argument is given, so you can archive output:

```console
$ git log -1 --pretty=%B | pycliphist add
Added clip 1.

$ pycliphist add "SELECT * FROM users;"
Added clip 2.
```

## 3. Browse and search

```console
$ pycliphist list --limit 5
$ pycliphist search "SELECT"
$ pycliphist search 'https?://\S+' --regex
```

## 4. Get a clip back out

```console
$ pycliphist get 2 --raw
SELECT * FROM users;

# write it straight back to a file
$ pycliphist get 2 --raw > query.sql
```

## 5. Machine-readable export

```console
$ pycliphist list --limit 100 --json > clips.json
$ python -c "import json;print(len(json.load(open('clips.json'))))"
2
```

## 6. Housekeeping

```console
$ pycliphist stats
$ pycliphist delete 2
$ pycliphist clear --yes
```

## 7. Isolated database for experiments

Point `PYCLIPHIST_DB` at a throwaway file so you never touch real history:

```console
$ export PYCLIPHIST_DB=/tmp/scratch-clips.db
$ pycliphist add "test" && pycliphist list
   1  2026-11-18 21:05:12  test
```

Run the whole walkthrough non-interactively:

```console
$ bash examples/demo.sh
```
