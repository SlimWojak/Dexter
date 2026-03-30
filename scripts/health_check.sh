#!/bin/bash
# Lab infrastructure health check
echo "=== Lab Health Check ==="
echo "Date: $(date -Iseconds)"
echo ""

# Qwen/vLLM
if curl -s http://localhost:8000/v1/models > /dev/null 2>&1; then
    MODEL=$(curl -s http://localhost:8000/v1/models | python3 -c "import sys,json; print(json.load(sys.stdin)['data'][0]['id'])" 2>/dev/null)
    echo "PASS: vLLM serving — $MODEL"
else
    echo "FAIL: vLLM not responding on :8000"
fi

# Constitution docs
CONST_COUNT=$(ls ~/lab/constitution/*.yaml ~/lab/constitution/*.md 2>/dev/null | wc -l)
echo "PASS: Constitution docs — $CONST_COUNT files" 

# Ground truth
GT_COUNT=$(ls ~/lab/constitution/ground_truth/*.yaml 2>/dev/null | wc -l)
echo "PASS: Ground truth — $GT_COUNT files"

# RiverWriter
if [ -d ~/lab/data/river/.git ]; then
    echo "PASS: RiverWriter repo present"
else
    echo "FAIL: RiverWriter not cloned"
fi

# Vault structure
VAULT_DIRS=$(find ~/lab/vault -type d | wc -l)
echo "PASS: Vault — $VAULT_DIRS directories"

# Disk
DISK_FREE=$(df -h /home/playground | tail -1 | awk {print })
echo "INFO: Disk free — $DISK_FREE"

echo ""
echo "=== Done ==="
