# lichess-tools

CLI tools for interacting with the Lichess chess API. Supports bulk study/account management and game analysis (finding moves with large eval swings).

## Installation

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/ckloote/lichess-tools.git
cd lichess-tools
uv venv
uv pip install -e .
```

The `lichess` command is now available in your virtual environment. Activate it or invoke it directly:

```bash
source .venv/bin/activate
lichess --help
```

## Authentication

Get a personal API token from <https://lichess.org/account/oauth/token>.

```bash
lichess config set-token YOUR_TOKEN
```

Or set the environment variable:

```bash
export LICHESS_TOKEN=YOUR_TOKEN
```

Check the current configuration:

```bash
lichess config show
```

## Commands

### `lichess studies`

**List studies** for a user:

```bash
lichess studies list
lichess studies list --username someuser
```

**Filter** results (filters are ANDed):

```bash
# Studies whose name matches a regex
lichess studies list --filter "name:~opening"

# Studies with 10 or more chapters
lichess studies list --filter "chapters:>=10"
```

**Delete** studies matching filters:

```bash
# Preview first (no changes made)
lichess studies delete --filter "name:~old" --dry-run

# Delete after confirmation prompt
lichess studies delete --filter "name:~old"
```

**Export** studies as PGN:

```bash
lichess studies export --filter "name:~repertoire" --output repertoire.pgn
```

---

### `lichess accounts`

**List blocked users:**

```bash
lichess accounts list-blocked
```

**Unblock** users matching filters:

```bash
# Preview
lichess accounts unblock --filter "username:~bot" --dry-run

# Unblock after confirmation
lichess accounts unblock --filter "username:~bot"
```

---

### `lichess games`

**Export games** as PGN:

```bash
lichess games export username
lichess games export username --since 2024-01-01 --output games.pgn
lichess games export username --since 2024-01-01 --until 2024-12-31 --perf blitz --max 200
```

**Analyze games** for critical moments (large eval swings):

```bash
lichess games analyze username
lichess games analyze username --since 2024-01-01
lichess games analyze username --blunder-threshold 150
```

This streams games with embedded Lichess cloud evaluations, identifies moves where the eval swings by more than the threshold (default: 100 centipawns), and stores results in a local SQLite database. A summary table is printed at the end.

---

## Filter syntax

| Pattern | Operator | Example |
|---|---|---|
| `key:value` | exact match | `result:1-0` |
| `key:~pattern` | regex match | `name:~sicilian` |
| `key:>=N` | greater than or equal | `chapters:>=5` |
| `key:<=N` | less than or equal | `likes:<=10` |
| `key:*text*` | contains | `name:*endgame*` |

Multiple `--filter` flags are ANDed together.

---

## Data storage

- **Config:** `~/.config/lichess-tools/config.toml`
- **Database:** `~/.local/share/lichess-tools/lichess.db`

The SQLite database stores game PGNs and critical moments. Inspect it directly:

```bash
sqlite3 ~/.local/share/lichess-tools/lichess.db
```

```sql
SELECT game_id, move_san, swing, color FROM critical_moments ORDER BY swing DESC LIMIT 20;
```
