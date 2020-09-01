#!/bin/bash

ROOT="$1"
FOLDER="$2"
INPUT="$3"
OUTPUT="$4"

function config {
    echo "$ROOT/config/$1"
}

DISABLE_FLOAT="$(config disable_float.tex)"

PDF_ENGINE="xelatex"
FONT_SIZE="13pt"
MARGIN="1in"

# Use fc-list to find font names
FONT_REG="DejaVu Serif"
FONT_MONO="DejaVu Sans Mono"

# FONT_OPTIONS="-V 'mainfont:$FONT_REG' -V 'monofont:$FONT_MONO'"
FONT_OPTIONS=""
PAGE_OPTIONS="-V fontsize=$FONT_SIZE -V geometry:margin=$MARGIN"

PDF_OPTIONS="-H $DISABLE_FLOAT --resource-path=$FOLDER --pdf-engine=$PDF_ENGINE $PAGE_OPTIONS $FONT_OPTIONS"

bash -c "pandoc $PDF_OPTIONS -o $OUTPUT $INPUT"