#!/bin/zsh -f
set -u

PROJECT_ROOT="/private/tmp/line-backup-legacy-false-positive/58"
CONFIG="$PROJECT_ROOT/config/line_backup_config.json"
STATE="$PROJECT_ROOT/state/backup_state.json"
DEST="/private/tmp/line-backup-legacy-false-positive/58/destination"
EXPECTED=57
SAMPLES=3
INTERVAL=5
OUT_DIR="/private/tmp/line-backup-legacy-false-positive/58/output"
TMP_DIR="$(mktemp -d /private/tmp/line-verify-only.XXXXXX)"
trap 'rm -rf "$TMP_DIR"' EXIT INT TERM

echo "LINE_ALBUM_BACKUP_RESULT"
echo "Mode: verify_only"
echo "Project root: $PROJECT_ROOT"
echo "Config: $CONFIG"
echo "State: $STATE"
echo "Destination: $DEST"
echo "Expected images: $EXPECTED"
echo "Configured group: $(jq -r '.group_name' "$CONFIG")"
echo "Configured group key: $(jq -r '.group_key' "$CONFIG")"
echo "State revision: $(jq -r '.revision' "$STATE")"
echo "Current run: $(jq -r '.current_run_id // "null"' "$STATE")"
echo "Active writer: $(jq -r '.active_writer_id // "null"' "$STATE")"

if [[ ! -f "$CONFIG" || ! -f "$STATE" ]]; then
  echo "LOAD_STATE=FAIL"
  exit 2
fi
jq -e . "$CONFIG" >/dev/null || { echo "CONFIG_PARSE=FAIL"; exit 2; }
jq -e . "$STATE" >/dev/null || { echo "STATE_PARSE=FAIL"; exit 2; }
echo "LOAD_STATE=PASS_READ_ONLY"

if [[ ! -d "$DEST" || -L "$DEST" ]]; then
  echo "DESTINATION=FAIL_MISSING_OR_SYMLINK"
  exit 3
fi

sample() {
  local sample_id="$1"
  local record="$TMP_DIR/sample-$sample_id.tsv"
  local entry_path rel type size mtime mime sha base lower
  local regular=0 images=0 subdirs=0 symlinks=0 other=0 metadata=0 zero=0 partial=0 unrecognized=0 total=0
  : > "$record"

  while IFS= read -r -d '' entry_path; do
    rel="${entry_path#$DEST/}"
    type="$(stat -f '%HT' -- "$entry_path")"
    if [[ "$type" == "Directory" ]]; then
      (( subdirs++ ))
      printf 'ENTRY|%s|DIRECTORY\n' "$rel" >> "$record"
      continue
    fi
    if [[ "$type" == "Symbolic Link" ]]; then
      (( symlinks++ ))
      printf 'ENTRY|%s|SYMLINK\n' "$rel" >> "$record"
      continue
    fi
    if [[ "$type" != "Regular File" ]]; then
      (( other++ ))
      printf 'ENTRY|%s|OTHER:%s\n' "$rel" "$type" >> "$record"
      continue
    fi

    (( regular++ ))
    size="$(stat -f '%z' -- "$entry_path")"
    mtime="$(stat -f '%m' -- "$entry_path")"
    mime="$(file --mime-type -b -- "$entry_path")"
    sha="$(shasum -a 256 -- "$entry_path" | awk '{print $1}')"
    base="${entry_path:t}"
    lower="${base:l}"
    (( total += size ))
    [[ "$size" == 0 ]] && (( zero++ ))
    if [[ "$lower" == .ds_store || "$base" == .*metadata* || "$lower" == *.part || "$lower" == *.partial || "$lower" == *.tmp || "$lower" == *.temp || "$lower" == *.download || "$lower" == *.crdownload || "$lower" == *.incomplete || "$lower" == *.filepart ]]; then
      [[ "$lower" == .ds_store || "$base" == .*metadata* ]] && (( metadata++ ))
      [[ "$lower" == *.part || "$lower" == *.partial || "$lower" == *.tmp || "$lower" == *.temp || "$lower" == *.download || "$lower" == *.crdownload || "$lower" == *.incomplete || "$lower" == *.filepart ]] && (( partial++ ))
    fi
    if [[ "$mime" == image/* && "$size" != 0 ]]; then
      (( images++ ))
      printf 'FILE|%s|%s|%s|%s|%s\n' "$rel" "$size" "$mtime" "$mime" "$sha" >> "$record"
    else
      (( unrecognized++ ))
      printf 'FILE|%s|%s|%s|%s|%s|UNRECOGNIZED\n' "$rel" "$size" "$mtime" "$mime" "$sha" >> "$record"
    fi
  done < <(find -P "$DEST" -mindepth 1 -maxdepth 1 -print0)

  local inventory_hash
  inventory_hash="$(shasum -a 256 "$record" | awk '{print $1}')"
  echo "SAMPLE=$sample_id"
  echo "REGULAR_FILES=$regular"
  echo "ACTUAL_IMAGES=$images"
  echo "SUBDIRECTORIES=$subdirs"
  echo "SYMLINKS=$symlinks"
  echo "OTHER_ENTRIES=$other"
  echo "TOTAL_BYTES=$total"
  echo "METADATA_FILES=$metadata"
  echo "ZERO_BYTE_FILES=$zero"
  echo "PARTIAL_TEMP_FILES=$partial"
  echo "UNRECOGNIZED_REGULAR_FILES=$unrecognized"
  echo "INVENTORY_SHA256=$inventory_hash"
  echo "---PER_FILE_SHA256_BYTE_LENGTH---"
  sort "$record"
  echo "---END_SAMPLE=$sample_id---"
  cp "$record" "$OUT_DIR/inventory-$sample_id.tsv"
}

sample 1
sleep "$INTERVAL"
sample 2
sleep "$INTERVAL"
sample 3

if cmp -s "$OUT_DIR/inventory-1.tsv" "$OUT_DIR/inventory-2.tsv" && cmp -s "$OUT_DIR/inventory-2.tsv" "$OUT_DIR/inventory-3.tsv"; then
  echo "STABLE_INVENTORY=PASS"
else
  echo "STABLE_INVENTORY=FAIL"
  exit 4
fi

if [[ "$(jq -r '.verified_albums[] | select(.fingerprint.start_date=="2024-05-13" and .fingerprint.end_date=="2024-05-17" and .fingerprint.expected_images==57) | .destinations[]' "$STATE")" == "$DEST" ]]; then
  echo "STATE_DESTINATION_REGISTRY=PASS"
else
  echo "STATE_DESTINATION_REGISTRY=FAIL"
  exit 5
fi

echo "FILESYSTEM_VERIFICATION=PASS"
echo "STATE_MUTATION=NONE"
echo "GUI_INPUT=NONE"
