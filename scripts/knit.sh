#!/bin/bash

# Note that this does not work with symlinks
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
ROOT="$( dirname $DIR )"

function config {
  echo "$ROOT/config/$1"
}

function script {
  echo "$DIR/$1"
}

# Config Files
PY="$(config python.sh)"
PANDOC="$(config pandoc.sh)"
VARS="$(config vars.py)"

# Scripts
TEMPLATE="$(script template.py)"

INPUT="$1"
OUTPUT="$2"

folder="$(dirname $INPUT)"

# mkdir -p "$folder"
if [ -s "$INPUT" ]; then
  base=$(basename $INPUT)

  # make the jinja file `.bin/folder/name-render.ext`
  JINJA=".bin/${folder}/${base%%.*}-render.${base##*.}"
  DEP="$JINJA.dep"

  if ! $PY $TEMPLATE -varfile $VARS -out $JINJA -dep $DEP "$OUTPUT" $INPUT; then
    exit 1
  fi
  $PANDOC $ROOT $folder $JINJA $OUTPUT
  RES=$?
  if [ $RES -ne 0 ]; then
    exit $RES
  fi
fi
echo "$INPUT -> $OUTPUT"
