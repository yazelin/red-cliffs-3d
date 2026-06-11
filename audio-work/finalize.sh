#!/bin/bash
# 定稿音檔後製:loudnorm 統一響度 + 頭尾 fade,輸出至 assets/
set -euo pipefail
cd "$(dirname "$0")"

declare -A PICKS=(
  [scene1]=329022 [scene2]=521367 [scene3]=670499 [scene4]=479328
  [scene5]=441319 [scene6]=621289 [scene7]=716385 [scene8]=789401
  [scene9]=621292 [battlecry]=563011 [chains]=529393
)

for slot in "${!PICKS[@]}"; do
  id=${PICKS[$slot]}
  src="candidates/${slot}-${id}.mp3"
  if [[ $slot == scene* ]]; then
    out="../assets/music/${slot}.mp3"; I=-18; fout=2
  else
    out="../assets/sfx/${slot}.mp3"; I=-16; fout=0.3
  fi
  [[ -f $src ]] || { echo "MISSING $src"; exit 1; }
  ffmpeg -y -loglevel error -i "$src" \
    -af "loudnorm=I=${I}:TP=-1.5:LRA=11,afade=t=in:d=1.2,areverse,afade=t=in:d=${fout},areverse" \
    -ar 44100 -b:a 128k "$out"
  echo "OK $slot <- #$id ($(du -h "$out" | cut -f1))"
done
echo all done
