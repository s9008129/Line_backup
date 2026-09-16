#!/bin/zsh -f
set -euo pipefail
umask 077

JQ=/usr/bin/jq
FILE=/usr/bin/file

if (( $# != 2 )); then
  print -u2 'usage: recovery-duplicate-fixture.sh STATE_JSON VERIFIED_DESTINATION'
  exit 2
fi

state_path="$1"
verified_destination="$2"
requested_group='旻謙允禎成長日記'
requested_key="line:jp.naver.line.mac:${requested_group}"
fingerprint_start='2024-05-13'
fingerprint_end='2024-05-17'
fingerprint_count=57

[[ -x "$JQ" ]] || { print -u2 "missing jq: $JQ"; exit 3; }
[[ -x "$FILE" ]] || { print -u2 "missing file: $FILE"; exit 3; }
[[ -f "$state_path" ]] || { print -u2 "missing state: $state_path"; exit 3; }
[[ -d "$verified_destination" ]] || { print -u2 "missing destination: $verified_destination"; exit 3; }

configured_key="$($JQ -r '.verified_albums[] | select(.fingerprint.start_date == $start and .fingerprint.end_date == $end and .fingerprint.expected_images == $count) | .group_key' \
  --arg start "$fingerprint_start" --arg end "$fingerprint_end" --argjson count "$fingerprint_count" "$state_path" | sed -n '1p')"
registry_destination_match="$($JQ -r --arg dest "$verified_destination" --arg start "$fingerprint_start" --arg end "$fingerprint_end" --argjson count "$fingerprint_count" '
  any(.verified_albums[]?;
    .fingerprint.start_date == $start and
    .fingerprint.end_date == $end and
    .fingerprint.expected_images == $count and
    (((.destinations // []) | index($dest)) != null)
  )
' "$state_path")"

if [[ "$registry_destination_match" == true && -n "$configured_key" ]]; then
  print 'CONFIGURED_IDENTITY_DUPLICATE_GATE=SKIPPED_VERIFIED'
  print 'CONFIGURED_IDENTITY_SIDE_EFFECTS=0'
else
  print 'CONFIGURED_IDENTITY_DUPLICATE_GATE=FAIL_FIXTURE_PRECONDITION'
  exit 4
fi

if [[ "$configured_key" != "$requested_key" ]]; then
  print "REQUESTED_IDENTITY_GATE=UNRESOLVED_CONFIGURED_KEY_MISMATCH"
  print 'REQUESTED_IDENTITY_SIDE_EFFECTS=0'
else
  print 'REQUESTED_IDENTITY_GATE=RESOLVED'
fi

fixture_root="$(mktemp -d /private/tmp/line-album-recovery-duplicate.XXXXXX)"
trap 'rm -rf -- "$fixture_root"' EXIT
fixture_destination="$fixture_root/destination"
mkdir -p "$fixture_destination"

first_image="$(find -P "$verified_destination" -type f -name '*.jpg' -print -quit)"
[[ -n "$first_image" ]] || { print -u2 'no source image found'; exit 5; }
cp -- "$first_image" "$fixture_destination/photo-001.jpg"
cp -- "$first_image" "$fixture_destination/photo-001.jpg.part"

actual_images=0
partial_files=0
zero_byte_files=0
regular_files=0
while IFS= read -r -d '' entry_path; do
  regular_files=$((regular_files + 1))
  relative_path="${entry_path#$fixture_destination/}"
  case "$relative_path" in
    *.part|*.partial|*.tmp|*.temp|*.download|*.crdownload|*.incomplete|*.filepart)
      partial_files=$((partial_files + 1))
      continue
      ;;
  esac
  entry_bytes="$(stat -f '%z' -- "$entry_path")"
  if (( entry_bytes == 0 )); then
    zero_byte_files=$((zero_byte_files + 1))
  fi
  entry_mime="$($FILE --brief --mime-type -- "$entry_path")"
  if [[ "$entry_mime" == image/* ]]; then
    actual_images=$((actual_images + 1))
  fi
done < <(find -P "$fixture_destination" -type f -print0)

[[ "$regular_files" == 2 && "$actual_images" == 1 && "$partial_files" == 1 && "$zero_byte_files" == 0 ]] || {
  print -u2 "interrupted fixture mismatch: regular=$regular_files images=$actual_images partial=$partial_files zero=$zero_byte_files"
  exit 6
}

fixture_state="$fixture_root/interrupted-state.json"
$JQ -n \
  --arg key "$configured_key" \
  --arg dest "$verified_destination" \
  --arg start "$fingerprint_start" \
  --arg end "$fingerprint_end" \
  --argjson count "$fingerprint_count" \
  '{schema_version:2,revision:1,current_run_id:"RUN-FIXTURE-INTERRUPTED",active_writer_id:"EXEC-FIXTURE",runs:[{
    run_id:"RUN-FIXTURE-INTERRUPTED",group_key:$key,destination:$dest,
    fingerprint:{start_date:$start,end_date:$end,expected_images:$count},
    intent_state:"INTENT_COMMITTED",dispatch_state:"UNKNOWN",
    intent:{intent_state:"INTENT_COMMITTED",dispatch_state:"UNKNOWN",save_all_retry_allowed:false}
  }]}' > "$fixture_state"

recovery_contract="$($JQ -r '
  .runs[0] as $run |
  if ($run.intent.intent_state == "INTENT_COMMITTED" and
      $run.dispatch_state == "UNKNOWN" and
      $run.intent.save_all_retry_allowed == false)
  then "PASS"
  else "FAIL"
  end
' "$fixture_state")"
[[ "$recovery_contract" == PASS ]] || { print -u2 'recovery contract fixture mismatch'; exit 7; }

print 'INTERRUPTED_DESTINATION=INCOMPLETE_OR_STILL_DOWNLOADING'
print 'INTERRUPTED_NEXT_STEP=READ_ONLY_VERIFY_ONLY_OR_BOUNDED_RECONCILIATION'
print 'DISPATCH_UNKNOWN_MANUAL_RECONCILIATION=YES'
print 'SAVE_ALL_RETRY=NO'
print 'SIDE_EFFECT_ACTIONS=0'
print 'RECOVERY_DUPLICATE_CONTRACT_FIXTURE=PASS'
