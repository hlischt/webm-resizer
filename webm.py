import math
import json
import random
import sys
import pathlib
import subprocess
import tempfile
import datetime
import shutil


def cyclic_resolution(frame_number: int, res: int) -> int:
    return math.ceil((res/4) * math.cos(frame_number / math.pi) + (res/4)*3)


def random_res(frame_number: int, res: int) -> int:
    return random.randint(2, 320)


def random_slow(frame_number: int, res: int) -> int:
    random.seed((frame_number//4) * res)
    return random.randint(2, 320)


def shrink(until: int):
    return lambda frame_num, res: \
        math.ceil((until + 1 - frame_num) * res)/(until + 1)


def ffprobe(path: pathlib.Path) -> dict:
    try:
        ffprobe_out = subprocess.run([
            'ffprobe',
            '-v', 'error',
            '-print_format', 'json',
            '-show_streams',
            '-select_streams', 'v:0',
            str(path),
        ], capture_output=True, check=True)
    except subprocess.CalledProcessError as e:
        raise ChildProcessError(e.stderr.decode()) from e
    return json.loads(ffprobe_out.stdout.decode())


def vid_info(j: dict) -> tuple:
    vid_json = j['streams'][0]
    return {
        'res': (vid_json['width'], vid_json['height']),
        'fps': vid_json['avg_frame_rate'],
    }


def ffmpeg_dump_frames(infile: pathlib.Path, outseq: pathlib.Path,
                       fps: str):
    '''Call ffmpeg to dump a sequence of frames in outdir.

    outseq is a pathlib object with a name like "./%03d.png".'''
    if not infile.exists():
        raise FileNotFoundError(f'{str(infile)} does not exist')
    if infile.is_dir():
        raise IsADirectoryError(f'{str(infile)} is a directory')
    if not outseq.parent.exists() or not outseq.parent.is_dir():
        raise NotADirectoryError(f'{str(outseq.parent)} is not a directory')
    try:
        subprocess.run([
            'ffmpeg', '-hide_banner', '-i',
            str(infile),
            '-an', '-sn', '-dn', '-vf', f'fps={fps}',
            str(outseq),
        ], capture_output=True, check=True)
    except subprocess.CalledProcessError as e:
        raise ChildProcessError('ffmpeg returned an error') from e


def ffmpeg_img2webm(infile: pathlib.Path, res: tuple, fps: str,
                    iteration: int, func):
    try:
        subprocess.run([
            'ffmpeg', '-hide_banner',
            '-r', fps,
            '-i', str(infile),
            '-an', '-sn', '-dn', '-vf',
            f'scale={func(iteration, res[0])}:'
            + f'{func(iteration, res[1])}'
            + ':flags=lanczos,setsar=1/1,'
            + f'fps={fps}',
            '-vcodec', 'libvpx-vp9',
            str(infile.with_suffix('.webm')),
        ], capture_output=True, check=True)
    except subprocess.CalledProcessError as e:
        raise ChildProcessError('ffmpeg returned an error') from e


def quote_file(path: pathlib.Path) -> str:
    '''Returns a quoted path, with escaped single quotes.'''
    return "'" + str(path.resolve()).replace("'", r"'\''") + "'"


def ffmpeg_concat(vid_list: pathlib.Path, orig_vid: pathlib.Path):
    try:
        subprocess.run([
            'ffmpeg', '-hide_banner', '-f', 'concat',
            '-safe', '0',
            '-i', str(vid_list),
            '-i', str(orig_vid),
            '-map', '0:v', '-map', '1:a',
            '-vcodec', 'copy',
            '-acodec', 'libopus', '-b:a', '96k',
            '-map_metadata', '-1',
            str(orig_vid.with_suffix('.out.webm')),
        ], check=True)
    except subprocess.CalledProcessError as e:
        raise ChildProcessError('ffmpeg returned an error') from e


def check_ff():
    probe = shutil.which('ffprobe') is None
    mpeg = shutil.which('ffmpeg') is None
    names = []
    if probe:
        names.append('ffprobe')
    if mpeg:
        names.append('ffmpeg')
    if len(names) > 0:
        sys.exit(f'Error: {" and ".join(names)} not found')


def main_func():
    random.seed(datetime.datetime.now().timestamp())
    check_ff()
    try:
        vid_path = pathlib.Path(sys.argv[1])
    except IndexError:
        sys.exit('Error: No file provided')
    if not vid_path.is_file():
        sys.exit(f'Error: {str(vid_path)} is not a valid file')
    with tempfile.TemporaryDirectory() as td:
        temp = pathlib.Path(td)
        vinfo = vid_info(ffprobe(vid_path))
        print(f'Creating PNG sequence as {temp / "%05d.png"}...',
              file=sys.stderr, end='')
        ffmpeg_dump_frames(vid_path, temp / '%05d.png', vinfo['fps'])
        print(' Done.', file=sys.stderr)
        pngs = sorted(list(temp.glob('./*.png')))
        webms = []
        concat_list = ''
        print('Converting PNG images to webm...',
              file=sys.stderr, end='')
        shrink_func = shrink(len(pngs))
        for idx, i in enumerate(pngs):
            ffmpeg_img2webm(i, vinfo['res'], vinfo['fps'],
                            idx, shrink_func)
            i.unlink()
            concat_list += f'file {quote_file(i.with_suffix(".webm"))}\n'
            webms.append(i.with_suffix('.webm'))
        print(' Done.', file=sys.stderr)
        with open(temp / 'list.txt', 'w', encoding='utf-8') as f:
            f.write(concat_list)
        ffmpeg_concat(temp / 'list.txt', vid_path)
        print('Deleting temporary files...', file=sys.stderr)
        for i in webms:
            i.unlink()
    print(f'Successfully encoded {vid_path.with_suffix(".out.webm")}',
          file=sys.stderr)


if __name__ == '__main__':
    main_func()
