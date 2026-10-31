#!/usr/bin/env bash
# Run ScienceClaw agent swarms on the GCP lab VM instead of the user's Mac.
# Runs ON the VM, from ~/oxt (copied there by remote/gcp_up.sh or rsync). Needs the Gemini key in ~/.gemini.key,
# which the user types themselves:  ssh -t <vm> 'bash ~/oxt/swarm/set_gemini_key.sh ~/.gemini.key'
#
#   bash remote/gcp_swarm.sh round1        # swarm/topics.txt        -> swarm/work/investigation_*.log
#   bash remote/gcp_swarm.sh round2        # swarm/topics_round2.txt -> swarm/work/round2_H*.log (same container)
#   TOPICS=swarm/my_topics.txt bash remote/gcp_swarm.sh custom
#
# Same safeguards as on the Mac (see SECURITY-REVIEW.md, ScienceClaw section): throwaway Docker container that
# sees only swarm/work and the key (read-only); every investigation --dry-run; Infinite pointed at a dead port.
set -euo pipefail
cd "$(dirname "$0")/.."
MODE="${1:-round1}"
KEY="${KEY:-$HOME/.gemini.key}"
[ -s "$KEY" ] || { echo "no Gemini key at $KEY; run: bash swarm/set_gemini_key.sh $KEY" >&2; exit 1; }
if ! command -v docker >/dev/null; then
  sudo apt-get -qq update && sudo apt-get -qq install -y docker.io >/dev/null
  sudo usermod -aG docker "$USER"
  exec sg docker -c "bash $0 $*"
fi
case "$MODE" in
  round1) bash swarm/run_scienceclaw_swarm.sh "$KEY" "$PWD/swarm/work" ;;
  round2) bash swarm/run_round2.sh "$PWD/swarm/work" ;;
  custom)
    : "${TOPICS:?set TOPICS=path/to/topics.txt (one investigation per line)}"
    TOPICS="$PWD/$TOPICS" TAG="${TAG:-custom}" bash swarm/run_round2.sh "$PWD/swarm/work" ;;
  *) echo "mode must be round1, round2 or custom" >&2; exit 2 ;;
esac
echo "swarm logs in $PWD/swarm/work; summarise them into swarm/SUMMARY.md (raw logs stay off GitHub)"
