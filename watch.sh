#!/bin/bash

# Watches all notes, and will render them as they are changed.

NOTES=$(find * -type d -not -path '*/.*')

cat <<-EOF
Waiting for changes in:
$NOTES

EOF

function backup {
  out=".backup/$1"
  mkdir -p "$(dirname $out)"
  cp -au $1 $out
}

make

inotifywait -q -m -e close_write,moved_to,create $NOTES |
while read -r directory events filename; do
  if [[ "$events" =~ "CLOSE_WRITE" ]] && ! [[ "$filename" =~ '.pdf' ]]; then

    echo "dir: ${directory}${filename} -> $events"
    # backup
    backup ${directory}${filename}
    make notes
  fi
done
