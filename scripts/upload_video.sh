#!/bin/bash

# Script to generate & Upload a video to YT Shorts with channel selection

# Check which interpreter to use (python)
if [ -x "$(command -v python3)" ]; then
  PYTHON=python3
else
  PYTHON=python
fi

# Read .mp/youtube.json file, loop through accounts array, get each id and print every id
youtube_ids=$($PYTHON -c "import json; print('\n'.join([account['id'] for account in json.load(open('.mp/youtube.json'))['accounts']]))")

echo "What account do you want to upload the video to?"

# Print the ids
for id in $youtube_ids; do
  echo $id
done

# Ask for the id
read -p "Enter the id: " account_id

# Check if the id is in the list
if [[ ! " ${youtube_ids[@]} " =~ " ${account_id} " ]]; then
  echo "ID not found"
  exit 1
fi

echo "ID found"

# Run python script (channel_id is optional - leave empty for default)
$PYTHON src/cron.py youtube $account_id