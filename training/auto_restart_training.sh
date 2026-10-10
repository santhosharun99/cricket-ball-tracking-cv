#!/bin/bash
# Restarts training after every round actually FINISHES (confirmed by a
# new line appearing in the run's results.csv), instead of guessing a
# fixed time limit. The earlier version used a blind 15-minute timer,
# which was too short - it kept killing round 3 just before it finished,
# over and over, for hours, with zero real progress. This version can't
# make that mistake: it only restarts once it SEES proof a round saved.
# MAX_WAIT is just a safety net in case something truly hangs.
cd ~/Downloads/cricket-ball-yolo/ball-training
MAX_WAIT=2400

count_lines() {
  RUN_DIR=$(ls -dt ~/runs/detect/yolo26_combined*/ 2>/dev/null | head -1)
  if [ -n "$RUN_DIR" ] && [ -f "${RUN_DIR}results.csv" ]; then
    wc -l < "${RUN_DIR}results.csv" | tr -d ' '
  else
    echo 0
  fi
}

while true; do
  BEFORE=$(count_lines)

  if ls -d ~/runs/detect/yolo26_combined* >/dev/null 2>&1; then
    echo "$(date): resuming from latest checkpoint (rounds saved so far: $BEFORE)" >> training_log.txt
    python3 resume_yolo26.py >> training_log.txt 2>&1 &
  else
    echo "$(date): starting fresh (no checkpoint yet)" >> training_log.txt
    python3 train_yolo26.py >> training_log.txt 2>&1 &
  fi

  WAITED=0
  while [ $WAITED -lt $MAX_WAIT ]; do
    sleep 30
    WAITED=$((WAITED+30))
    AFTER=$(count_lines)
    if [ "$AFTER" -gt "$BEFORE" ]; then
      echo "$(date): confirmed a new round finished and saved - restarting fresh" >> training_log.txt
      break
    fi
  done

  if [ $WAITED -ge $MAX_WAIT ]; then
    echo "$(date): WARNING - 40 minutes passed with no new round saved, restarting anyway" >> training_log.txt
  fi

  ps aux | awk '/resume_yolo26.py|train_yolo26.py/ && !/awk/ {print $2}' | xargs -r kill -9
  sleep 5
done
