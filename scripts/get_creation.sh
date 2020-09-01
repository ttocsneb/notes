#!/bin/bash

if ! [ -z $(git ls-files $1) ]; then
  DATE="$(git log --date=iso --format='%ad' --follow -- $1 | tail -1)"
else
  STAT="$(stat -c '%w|%y' $1)"
  CREATED="$(echo $STAT | grep -Po '.*(?=\|)' )"
  CHANGED="$(echo $STAT | grep -Po '(?<=\|).*')"
  if [[ "$CREATED" != '-' ]]; then
    DATE="$CREATED"
  else
    DATE="$CHANGED"
  fi
fi

echo $(date --date="$DATE" '+%s')
