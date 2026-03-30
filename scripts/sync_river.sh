#!/bin/bash
# Daily RiverWriter data sync
cd ~/lab/data/river && git pull --ff-only 2>&1
echo "$(date -Iseconds) river sync complete" >> ~/lab/logs/sync.log
