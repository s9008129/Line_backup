#!/bin/zsh -f
set -u

files=(
  "/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/LINE-BACKUP-GOAL-HANDOFF-2026-09-15.md"
  "/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/evidence/20260915-capability-matrix.md"
  "/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/evidence/20260915-audit-summary.md"
  "/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/evidence/20260915-recovery-duplicate-fixture.sh"
  "/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/evidence/20260915-recovery-duplicate-fixture/attempt-01/stdout.log"
  "/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/evidence/20260915-recovery-duplicate-fixture/attempt-01/stderr.log"
  "/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/evidence/20260915-recovery-duplicate-fixture/attempt-01/exit-code"
  "/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/evidence/20260915-recovery-duplicate-fixture/attempt-02/stdout.log"
  "/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/evidence/20260915-recovery-duplicate-fixture/attempt-02/stderr.log"
  "/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/evidence/20260915-recovery-duplicate-fixture/attempt-02/exit-code"
  "/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/evidence/20260915-verify-only-57/verify-only.sh"
  "/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/evidence/20260915-verify-only-57/stdout.log"
  "/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/evidence/20260915-verify-only-57/stderr.log"
  "/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/evidence/20260915-verify-only-57/exit-code"
  "/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/evidence/20260915-verify-only-57/inventory-1.tsv"
  "/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/evidence/20260915-verify-only-57/inventory-2.tsv"
  "/Users/hsiaojohnny/Documents/ChatGPT/Line_backup/evidence/20260915-verify-only-57/inventory-3.tsv"
  "/Users/hsiaojohnny/Documents/Codex/2026-09-07/line-album-backup-line-backup-state/config/line_backup_config.json"
  "/Users/hsiaojohnny/Documents/Codex/2026-09-07/line-album-backup-line-backup-state/state/backup_state.json"
  "/Users/hsiaojohnny/Documents/Codex/2026-09-07/line-album-backup-line-backup-state/state/run_log.md"
  "/Users/hsiaojohnny/Documents/Codex/2026-09-12/files-pasted-by-the-user-line/.agent/tasks/T20260914-0120-01-c04-observation-architecture/plan.md"
  "/Users/hsiaojohnny/Documents/Codex/2026-09-12/files-pasted-by-the-user-line/.agent/tasks/T20260914-0120-01-c04-observation-architecture/handoff.md"
  "/Users/hsiaojohnny/Documents/Codex/2026-09-12/files-pasted-by-the-user-line/.agent/tasks/T20260914-0120-01-c04-observation-architecture/execution.md"
  "/Users/hsiaojohnny/Documents/Codex/2026-09-12/files-pasted-by-the-user-line/.agent/tasks/T20260914-0120-01-c04-observation-architecture/review/attempt-33/coordinator-receipt.md"
  "/Users/hsiaojohnny/.codex/skills/line-album-backup/SKILL.md"
  "/Users/hsiaojohnny/.codex/skills/line-album-backup/references/state-contract.md"
  "/Users/hsiaojohnny/.codex/skills/line-album-backup/references/state-machine.md"
  "/Users/hsiaojohnny/.codex/skills/line-album-backup/references/ui-procedure.md"
  "/Users/hsiaojohnny/.codex/skills/line-album-backup/references/verification.md"
  "/Users/hsiaojohnny/.codex/skills/line-album-backup/schemas/schemas.json"
  "/Users/hsiaojohnny/Library/Application Support/LineNativeAXGUIBridge/bin/line-native-ax-gui-session-bridge"
  "/Users/hsiaojohnny/Library/Application Support/LineNativeAXGUIBridge/bin/line-native-ax-readonly-scrollbar-probe"
  "/Users/hsiaojohnny/Library/Application Support/LineNativeAXGUIBridge/deployment-manifest.json"
  "/Users/hsiaojohnny/Library/Application Support/LineNativeAXGUIBridge/daemon.status.json"
  "/Users/hsiaojohnny/Library/Application Support/LineNativeAXGUIBridge/daemon.lock"
  "/Users/hsiaojohnny/Library/LaunchAgents/com.openai.line-native-ax-gui-session-bridge.plist"
  "/Users/hsiaojohnny/Documents/Codex/2026-09-12/line-native-ax-gui-session-bridge/work/release/line-native-ax-gui-session-bridge"
  "/Users/hsiaojohnny/Documents/Codex/2026-09-12/line-native-ax-gui-session-bridge/work/release/line-native-ax-readonly-scrollbar-probe"
)

missing=0
for entry in "${files[@]}"; do
  if [[ ! -f "$entry" ]]; then
    echo "MISSING|$entry"
    missing=1
    continue
  fi
  bytes="$(stat -f '%z' -- "$entry")"
  sha="$(shasum -a 256 -- "$entry" | awk '{print $1}')"
  printf 'ARTIFACT|%s|bytes=%s|sha256=%s\n' "$entry" "$bytes" "$sha"
done

if (( missing )); then
  exit 1
fi
