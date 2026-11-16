# AnthroForge — the app

Code foundation for AnthroForge as a real application (not a web page),
built to [`APP_BLUEPRINT.md`](../anthroforge-v2/APP_BLUEPRINT.md) in the
sibling design folder. This repo is the **Phase-1 MVP scaffold**
(blueprint §15): the Python Core Service skeleton that both the future
GUI and the MCP server will be thin clients of (§2.1, §2.3). The shell
(Tauri 2, §2.2 — decision D1) is deliberately **not** here yet; no Rust
or Electron toolchain is needed to build or test anything in this repo.

## Layout → blueprint map

| Path | What it is | Blueprint |
|---|---|---|
| `core/` | The Core Service package (single implementation of all non-pixel logic) | §2.3 |
| `core/character.py` | Character record (`.afchar.json`): load/save, schema version, validation | §3.1 |
| `core/sharecode.py` | Share-code codec: record − provenance → canonical JSON → zlib → +CRC32 → base64url, `AF1-` prefix | §3.2, CREATOR_LESSONS R2 |
| `core/sliders.py` | Canonical slider records + registry (range clamp, safe-range warnings) | §3.3, MAKEHUMAN_OMNIVERSAL §6.1 |
| `core/errors.py` | Named error types; every failure names its field/file/id | §4.6 (applied to the library layer) |
| `core/bases.py` | Base registry: base records + geometry packages (hm08, hm08 masculine) | §3.6 |
| `core/geometry.py` | .target parsing, canonical instance packs, field evaluation (incl. gravity-coupled decomposition), fold gate, GLB writer | §3.3 |
| `core/build.py` | The build service: character → validate → couplings → geometry → fold gate → GLB → QA gauntlet | §2.3 |
| `core/fur.py` | Fur data: species coat profiles + platform budgets, validated | §3.6 |
| `mcp/` | MCP server package — catalogue + live handlers for `validate_character` / `export_run`; no transport yet | §4 |
| `mcp/server.py` | All 28 specced tool rows (32 callable names — rows 5/21/28 name 2–3 tools each); Phase-1 MVP subset flagged | §4.3, §15 Phase 1 item 4 |
| `library/` | The user-visible library folder (plain files; SQLite index comes later as a rebuildable cache) | §2.5, §3.6 |
| `library/sliders/` | Canonical slider records, `<id>.json` — 74 records (see INTEGRATION.md) | §3.6 |
| `library/bases/` | Base records + geometry packages (`.npz`) | §3.6 |
| `library/instances/` | Canonical-precision per-base slider fields (`.npz` packs) | §3.6 |
| `library/presets/` | The six spec'd presets (`.afchar.json`) + `INDEX.json` with share codes | §3.6 |
| `library/fur/` | Species coat profiles + fur budgets (JSON) | §3.6 |
| `library/{parts,teeth,materials,characters,intake,exports}/` | Empty for now (`.gitkeep`), filled by their phases | §3.6 |
| `tests/` | pytest suite (see below) | §15 acceptance, in miniature |
| `pyproject.toml` | Project metadata + pytest config. Core deps: stdlib + numpy (geometry layer) | — |

## The seed sliders (`library/sliders/`)

> **Nov 12, 2026:** the library has grown well past the seed set —
> 74 records, 11 sliders with hm08 geometry, 2 bases, 6 presets.
> See **INTEGRATION.md** for the full inventory and what remains
> record-only. The original three seed records:

Three canonical records, all grounded in data already on disk — no
invented morphs:

| id | Source | Licence tier |
|---|---|---|
| `body.belly.protrusion` | Fat Males exact-topology morph: max \|delta\| 0.156057 m at the navel, mean 0.036993 m over 2,024 verts (`character_assets/learned/fat-males_body_morph.json/.npz`) | study-only (internal) |
| `body.chubby` | HIMBO V5 "BodyChubby" decoded from BodySlide `.osd`: 9,229 of 9,346 verts, max \|delta\| 0.057088 m (converted at 0.01428 m/Skyrim unit) | study-only (internal) |
| `head.brow.projection` | Craniometric index from `brow-study.md`: 0 = recent modern human, +100 = Krapina Neanderthal, species presets at −20…−45 | build (published-data derivation) |

Per blueprint decision D6, the two study-only records are internal
until re-authored from build-tier sources; their tier travels in the
record's provenance, as §6.1 requires.

## Validation contract

- **Structural** errors (wrong `format`, unsupported `version`, unknown
  top-level field, non-numeric slider value, part entry without a
  slot…) raise `SchemaError` naming the field, at load time.
- **Semantic** validation (`Character.validate(registry)`) returns a
  report: unknown slider ids are named **errors** (and are *kept* in
  the record — failure is reported, data is not silently dropped);
  out-of-range values are clamped in place with each clamp returned as
  a **warning**; values inside the range but outside a record's safe
  band are kept, with a `"safe"` warning (the record's fold-risk
  disclosure).

## Share codes

```python
from core import Character, encode_share_code, decode_share_code
code = encode_share_code(Character(name="…", sliders={"body.belly.protrusion": 0.62}))
char = decode_share_code(code)   # sliders round-trip bit-for-bit
```

A typical sparse character encodes to ~290 characters (§3.2 estimates
200–600). Flipping any character in the code fails the CRC32 checksum
with a named `ShareCodeError` before the payload is trusted.

## Tests

```bash
python3 -m pytest          # 26 tests, stdlib-only code under test
```

(pytest itself is the only test dependency; it was installed user-level
with `pip3 install --user --break-system-packages pytest`.)

Covered: character file + dict round-trips (lossless), schema rejection
by field name, share-code round-trip (including non-tidy doubles and
1e-09), provenance stripping, deterministic encoding, mid-code
corruption → checksum error, prefix/version rejection, registry load of
the seed records, range clamping (both poles), safe-range warnings,
unknown-slider reporting through `Character.validate`, and the
filename↔id naming rule.

## Decisions taken where the blueprint left room

1. **Share-code checksum placement**: CRC32 of the *compressed* bytes,
   appended as 4 big-endian bytes before base64url (§3.2 specced
   "deflate + base64url + prefix" but no checksum; the task required
   corruption detection). Padding is stripped on encode, restored on
   decode.
2. **Registry instances list only what exists.** The omniversal doc's
   belly record lists aspirational mh08/af2 instances; the seed record
   here lists only the `skyrim_fatmales` instance whose file exists,
   with the exact-topology QA. Untransferred sliders have empty
   `instances` (brow) rather than placeholder files.
3. **Clamp split**: `[min, max]` is a hard clamp; the safe band only
   warns. §6.1 ships both numbers without saying which one clamps —
   hard-clamping to the safe band would make the declared range a lie.
4. **Unknown top-level fields are rejected**, not ignored (§3.1 doesn't
   say). A character file stays diff-able and typos surface at load.
   Unknown *slider ids*, by contrast, are report-errors, not load
   errors, so a character from a richer library still opens.
5. **`base` merges over defaults**: a record naming only a head keeps
   the default body id, rather than failing.
6. **MCP stub shape**: `mcp/server.py` exposes the tool catalogue +
   a `call_tool` that raises `NotImplementedError` per tool. No MCP
   SDK dependency until the transport phase — the SDK choice belongs
   with the shell work, and the stub must not pretend to be a server.
7. **`species_preset` may be `null`** and `fur.profile` may be `null`
   (both appear in §3.1's example in those forms).

## Not in this scaffold (by design)

Tauri shell + frontend split, Blender sidecar (§2.4), SQLite index
(§2.5), slider *engine* (applying instances to meshes, §2.3/§6.2), the
Fat Males belly → hm08 first-proof transfer (§15 Phase 1 item 3 — the
MVP acceptance test), MCP transport + handlers, GLB export gauntlet
(§11.1). The record/registry/codec layer they all stand on is what's
here, tested.
