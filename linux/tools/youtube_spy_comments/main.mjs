#!/usr/bin/env node
import { spawn } from 'node:child_process';

function parseArgs() {
  const args = process.argv.slice(2);
  let params = {};
  const pIdx = args.indexOf('--params');
  if (pIdx !== -1 && args[pIdx + 1]) {
    try {
      params = JSON.parse(args[pIdx + 1]);
    } catch (_) {}
  }
  return params;
}

const params = parseArgs();
const target = params.target || params.url || params.content_or_transcript;

if (!target) {
  console.log(JSON.stringify({
    status: 'ERROR',
    tool: 'youtube_spy_comments',
    error: 'Target URL or video ID is required.',
    analyzed_at: new Date().toISOString()
  }, null, 2));
  process.exit(1);
}

const limit = Math.max(1, Math.min(100, parseInt(params.limit || 20, 10)));

const pyScript = `
import sys
import json
import yt_dlp

target = sys.argv[1]
limit = int(sys.argv[2])

ydl_opts = {
    'getcomments': True,
    'extractor_args': {
        'youtube': {
            'max_comments': [str(limit), str(limit), '0', '0', '1']
        }
    },
    'skip_download': True,
    'quiet': True,
    'no_warnings': True
}

try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(target, download=False)
        raw_comments = info.get('comments') or []
        
        parsed_comments = []
        for c in raw_comments[:limit]:
            parsed_comments.append({
                'id': c.get('id'),
                'author': c.get('author'),
                'author_id': c.get('author_id'),
                'text': c.get('text'),
                'like_count': c.get('like_count', 0),
                'timestamp': c.get('timestamp'),
                'time_text': c.get('time_text'),
                'is_favorited': c.get('is_favorited', False)
            })
            
        result = {
            'status': 'SUCCESS',
            'tool': 'youtube_spy_comments',
            'target': target,
            'video_id': info.get('id'),
            'video_title': info.get('title'),
            'total_comments_retrieved': len(parsed_comments),
            'comments': parsed_comments,
            'analyzed_at': info.get('upload_date')
        }
        print(json.dumps(result))
except Exception as e:
    err_res = {
        'status': 'ERROR',
        'tool': 'youtube_spy_comments',
        'target': target,
        'error': str(e)
    }
    print(json.dumps(err_res))
    sys.exit(1)
`;

const proc = spawn('python3', ['-c', pyScript, target, String(limit)]);
let stdoutData = '';
let stderrData = '';

proc.stdout.on('data', (d) => {
  stdoutData += d.toString();
});

proc.stderr.on('data', (d) => {
  stderrData += d.toString();
});

proc.on('close', (code) => {
  if (code === 0 && stdoutData.trim()) {
    try {
      const parsed = JSON.parse(stdoutData.trim());
      console.log(JSON.stringify(parsed, null, 2));
      process.exit(0);
    } catch (_) {
      console.log(stdoutData.trim());
      process.exit(0);
    }
  } else {
    try {
      const parsed = JSON.parse(stdoutData.trim());
      console.log(JSON.stringify(parsed, null, 2));
    } catch (_) {
      console.log(JSON.stringify({
        status: 'ERROR',
        tool: 'youtube_spy_comments',
        target,
        error: stderrData.trim() || 'Failed to extract comments.'
      }, null, 2));
    }
    process.exit(code || 1);
  }
});
