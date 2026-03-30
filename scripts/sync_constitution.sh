#!/bin/bash
# Weekly constitution sync from en1gma repo
# Pulls methodology docs — constitution is READ ONLY in the lab
EN1GMA_REPO="https://github.com/SlimWojak/en1gma.git"
TMP_DIR=$(mktemp -d)

git clone --depth 1 --sparse "$EN1GMA_REPO" "$TMP_DIR" 2>/dev/null
cd "$TMP_DIR"
git sparse-checkout set en1gma/methodology en1gma/ground_truth 2>/dev/null

# Copy methodology
cp -f "$TMP_DIR/en1gma/methodology/SYNTHETIC_OLYA_METHOD_vLOCK.yaml" ~/lab/constitution/vLOCK.yaml 2>/dev/null
cp -f "$TMP_DIR/en1gma/methodology/STATE_DETECTION_LOGIC_v2.yaml" ~/lab/constitution/STATE_DETECTION_v2.yaml 2>/dev/null
cp -f "$TMP_DIR/en1gma/methodology/ARS_CANON_v1_3.md" ~/lab/constitution/ARS_CANON_v1_3.md 2>/dev/null
cp -f "$TMP_DIR/en1gma/methodology/calibration_results.yaml" ~/lab/constitution/calibration_results.yaml 2>/dev/null
cp -f "$TMP_DIR/en1gma/methodology/HTF_MAP_SPEC_v0_1.yaml" ~/lab/constitution/HTF_MAP_SPEC_v0_1.yaml 2>/dev/null

# Copy ground truth
cp -f "$TMP_DIR/en1gma/ground_truth/"*.yaml ~/lab/constitution/ground_truth/ 2>/dev/null

rm -rf "$TMP_DIR"
echo "$(date -Iseconds) constitution sync complete" >> ~/lab/logs/sync.log
