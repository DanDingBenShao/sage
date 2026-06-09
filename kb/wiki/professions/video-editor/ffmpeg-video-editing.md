---
title: ffmpeg 视频编辑常用命令
description: >
  ffmpeg 命令行视频编辑的常用操作：无损剪切、合并拼接、缩放裁剪、交叉淡入淡出转场、字幕烧录、文字叠加、GIF 转换。适合脚本批处理和快速操作。
type: tool
domain: [video-production, software-dev]
source: web-searched
source_detail: [ffmpeg docs, community wikis, 2025]
related: [[video-editing-pipeline]], [[screen-recording-setup]], [[video-transitions-guide]]
created: 2026-06-09
updated: 2026-06-09
confidence: high
---

# ffmpeg 视频编辑常用命令

> **注意**: ffmpeg 适合精确、批量和脚本化操作。交互式剪辑用 DaVinci Resolve 或剪映。

## 无损剪切 (不重编码，秒级完成)

```bash
# 从 00:01:30 开始截取 60 秒 (关键帧对齐，可能有几秒偏差)
ffmpeg -ss 00:01:30 -i input.mp4 -t 60 -c copy output.mp4

# 精确剪切 (重编码，但帧精确)
ffmpeg -ss 00:01:30 -i input.mp4 -t 60 -c:v libx264 -crf 18 -c:a aac output.mp4

# 剪切到某时间点结束
ffmpeg -i input.mp4 -to 00:05:00 -c copy output.mp4
```

## 合并/拼接

```bash
# 方法 1: concat demuxer (同格式，无损)
# 先创建 filelist.txt:
#   file 'part1.mp4'
#   file 'part2.mp4'
#   file 'part3.mp4'
ffmpeg -f concat -safe 0 -i filelist.txt -c copy merged.mp4

# 方法 2: concat filter (不同格式/需要转场)
ffmpeg -i part1.mp4 -i part2.mp4 -filter_complex \
  "[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[outv][outa]" \
  -map "[outv]" -map "[outa]" merged.mp4
```

## 交叉淡入淡出转场

```bash
# 两段视频之间加 0.5 秒 crossfade
ffmpeg -i part1.mp4 -i part2.mp4 -filter_complex \
  "[0:v]settb=AVTB,fps=30[v0]; \
   [1:v]settb=AVTB,fps=30[v1]; \
   [v0][v1]xfade=transition=fade:duration=0.5:offset=4.5[outv]; \
   [0:a][1:a]acrossfade=d=0.5[outa]" \
  -map "[outv]" -map "[outa]" output.mp4

# offset = 第一个视频的时长 - transition 时长
```

## 缩放与裁剪

```bash
# 缩放到 1080p (保持宽高比，加黑边)
ffmpeg -i input.mp4 -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2" output.mp4

# 裁剪到 16:9 (从中心)
ffmpeg -i input.mp4 -vf "crop=ih*16/9:ih" output.mp4

# 裁剪指定区域 (x, y, width, height)
ffmpeg -i input.mp4 -vf "crop=800:600:100:50" output.mp4
```

## 字幕烧录

```bash
# SRT 字幕烧录进画面
ffmpeg -i input.mp4 -vf "subtitles=subs.srt:force_style='FontSize=20,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=2'" output.mp4

# ASS 字幕 (支持样式)
ffmpeg -i input.mp4 -vf "ass=subs.ass" output.mp4
```

## 文字叠加 (drawtext)

```bash
# 底部居中文字
ffmpeg -i input.mp4 -vf \
  "drawtext=text='你的文字':fontsize=48:fontcolor=white:borderw=3:bordercolor=black: \
   x=(w-text_w)/2:y=h-th-80" output.mp4

# 带半透明黑底框
ffmpeg -i input.mp4 -vf \
  "drawbox=y=ih-ih/4:w=iw:h=ih/4:color=black@0.5:t=fill, \
   drawtext=text='文字':fontsize=32:fontcolor=white: \
   x=(w-text_w)/2:y=h-th-h/8" output.mp4
```

## GIF 转换 (高质量)

```bash
# 两 pass 方法 (palettegen + paletteuse)
ffmpeg -i input.mp4 -vf "fps=15,scale=800:-1:flags=lanczos,palettegen=stats_mode=diff" palette.png
ffmpeg -i input.mp4 -i palette.png -filter_complex "fps=15,scale=800:-1:flags=lanczos[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=5" output.gif

# 高质量关键帧抖动
ffmpeg -i input.mp4 -vf "fps=10,scale=640:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=128:stats_mode=diff[p];[s1][p]paletteuse=dither=bayer:bayer_scale=5" output.gif
```

## 提取音频

```bash
# 提取音频为 WAV (Whisper 转录用)
ffmpeg -i input.mp4 -vn -acodec pcm_s16le -ar 16000 -ac 1 audio.wav

# 提取音频为 MP3
ffmpeg -i input.mp4 -vn -c:a libmp3lame -b:a 192k audio.mp3
```

## 批量操作模板

```bash
# 批量将文件夹内所有 MP4 转为统一格式
for f in *.mp4; do
  ffmpeg -i "$f" -c:v libx264 -preset fast -crf 23 -c:a aac -b:a 128k "converted/${f%.mp4}.mp4"
done
```
