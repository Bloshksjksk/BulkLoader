import os, time, math, shutil, pyromod.listen, asyncio, random, shlex
from urllib.parse import unquote
from urllib.error import HTTPError
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Message
from pyrogram.errors import BadRequest
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from typing import Tuple
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configs
API_HASH = os.environ.get('API_HASH') # Api hash
APP_ID = int(os.environ.get('APP_ID')) # Api id/App id
BOT_TOKEN = os.environ.get('BOT_TOKEN') # Bot token
OWNER_ID = os.environ.get('OWNER_ID') # Your telegram id
AS_ZIP = bool(os.environ.get('AS_ZIP', False)) # Upload method. If True: will Zip all your files and send as zipfile | If False: will send file one by one
BUTTONS = bool(os.environ.get('BUTTONS', False)) # Upload mode. If True: will send buttons (Zip or One by One) instead of AZ_ZIP | If False: will do as you've fill on AZ_ZIP

# Buttons
done_text = "Your Task has Been Done."
inline_keyboard = InlineKeyboardMarkup(
    [
        # Create a list of InlineKeyboardButton objects
        [
            InlineKeyboardButton("Gᵢᵥₑ ₐ ₕₑₐᵣₜ💖",url="https://t.me/movie_time_botonly")
        ]
    ]
)
START_BUTTONS=[
    [
        InlineKeyboardButton("🏆𝙏𝙍𝙐𝙈𝘽𝙊𝙏𝙎🏆", url="https://t.me/movie_time_botonly")
    
    ],
    [InlineKeyboardButton("☀️𝘾𝙍𝙀𝘼𝙏𝙊𝙍☀️", url="https://t.me/fligher")],
]

CB_BUTTONS=[
    [
        InlineKeyboardButton("𝐙𝐢𝐩🗜️", callback_data="zip"),
        InlineKeyboardButton("𝐎𝐧𝐞 𝐛𝐲 𝐨𝐧𝐞📃", callback_data="1by1"),
    ]
]

# Helpers

# https://github.com/SpEcHiDe/AnyDLBot
async def progress_for_pyrogram(
    current,
    total,
    ud_type,
    message,
    start
):
    now = time.time()
    diff = now - start
    if round(diff % 10.00) == 0 or current == total:
        # if round(current / total * 100, 0) % 5 == 0:
        percentage = current * 100 / total
        speed = current / diff
        elapsed_time = round(diff) * 1000
        time_to_completion = round((total - current) / speed) * 1000
        estimated_total_time = elapsed_time + time_to_completion

        elapsed_time = TimeFormatter(milliseconds=elapsed_time)
        estimated_total_time = TimeFormatter(milliseconds=estimated_total_time)

        progress = "[{0}{1}] \nP: {2}%\n".format(
            ''.join(["█" for i in range(math.floor(percentage / 5))]),
            ''.join(["░" for i in range(20 - math.floor(percentage / 5))]),
            round(percentage, 2))

        tmp = progress + "{0} of {1}\nSpeed: {2}/s\nETA: {3}\n".format(
            humanbytes(current),
            humanbytes(total),
            humanbytes(speed),
            # elapsed_time if elapsed_time != '' else "0 s",
            estimated_total_time if estimated_total_time != '' else "0 s"
        )
        try:
            await message.edit(
                text="{}\n {}".format(
                    ud_type,
                    tmp
                )
            )
        except:
            pass


def humanbytes(size):
    # https://stackoverflow.com/a/49361727/4723940
    # 2**10 = 1024
    if not size:
        return ""
    power = 2**10
    n = 0
    Dic_powerN = {0: ' ', 1: 'Ki', 2: 'Mi', 3: 'Gi', 4: 'Ti'}
    while size > power:
        size /= power
        n += 1
    return str(round(size, 2)) + " " + Dic_powerN[n] + 'B'


def TimeFormatter(milliseconds: int) -> str:
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = ((str(days) + "d, ") if days else "") + \
        ((str(hours) + "h, ") if hours else "") + \
        ((str(minutes) + "m, ") if minutes else "") + \
        ((str(seconds) + "s, ") if seconds else "") + \
        ((str(milliseconds) + "ms, ") if milliseconds else "")
    return tmp[:-2]


async def run_cmd(cmd) -> Tuple[str, str, int, int]:
    if type(cmd) == str:
        cmd = shlex.split(cmd)
    process = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    return (
        stdout.decode("utf-8", "replace").strip(),
        stderr.decode("utf-8", "replace").strip(),
        process.returncode,
        process.pid,
    )


# Send media; required ffmpeg
async def send_media(file_name: str, update: Message) -> bool:
    if os.path.isfile(file_name):
        files = file_name
        pablo = update
        if not '/' in files:
            caption = files
        else:
            caption = files.split('/')[-1]
        progress_args = ('📥𝙐𝙥𝙡𝙤𝙖𝙙𝙞𝙣𝙜 𝙩𝙤 𝙔𝙤𝙪𝙧 𝙩𝙚𝙡𝙚𝙜𝙧𝙖𝙢 𝙘𝙝𝙖𝙩 𝙥𝙡𝙚𝙖𝙨𝙚 𝙬𝙖𝙞𝙩 𝘽𝙖𝙨𝙚𝙙 𝙤𝙣 𝙁𝙞𝙡𝙚 𝙎𝙞𝙯𝙚 𝙞𝙩 𝙬𝙞𝙡𝙡 𝙏𝙖𝙠𝙚 𝙎𝙤𝙢𝙚 𝙩𝙞𝙢𝙚...', pablo, time.time())
        if files.lower().endswith(('.mkv', '.mp4')):
            metadata = extractMetadata(createParser(files))
            duration = 0
            if metadata is not None:
                if metadata.has("duration"):
                    duration = metadata.get('duration').seconds
            rndmtime = str(random.randint(0, duration))
            await run_cmd(f'ffmpeg -ss {rndmtime} -i "{files}" -vframes 1 thumbnail.jpg')
            await update.reply_video(files, caption=caption, duration=duration, thumb='thumbnail.jpg', progress=progress_for_pyrogram, progress_args=progress_args)
            # os.remove('thumbnail.jpg')
        elif files.lower().endswith(('.jpg', '.jpeg', '.png')):
            try:
                await update.reply_photo(files, caption=caption, progress=progress_for_pyrogram, progress_args=progress_args,reply_markup=inline_keyboard)
            except Exception as e:
                print(e)
                await update.reply_document(files, caption=caption, progress=progress_for_pyrogram, progress_args=progress_args,reply_markup=inline_keyboard)
        elif files.lower().endswith(('.mp3')):
            try:
                await update.reply_audio(files, caption=caption, progress=progress_for_pyrogram, progress_args=progress_args,reply_markup=inline_keyboard)
            except Exception as e:
                print(e)
                await update.reply_document(files, caption=caption, progress=progress_for_pyrogram, progress_args=progress_args,reply_markup=inline_keyboard)
        else:
            await update.reply_document(files, caption=caption, progress=progress_for_pyrogram, progress_args=progress_args,reply_markup=inline_keyboard)
        return True
    else:
        return False


async def download_file(url, dl_path):
    command = [
        'yt-dlp',
        '-f', 'best',
        '-i',
        '-o',
        dl_path+'/%(title)s.%(ext)s',
        url
    ]
    await run_cmd(command)


# https://github.com/MysteryBots/UnzipBot/blob/master/UnzipBot/functions.py
async def absolute_paths(directory):
    for dirpath, _, filenames in os.walk(directory):
        for f in filenames:
            yield os.path.abspath(os.path.join(dirpath, f))


# Running bot
xbot = Client('BulkLoader', api_id=APP_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


if OWNER_ID:
    OWNER_FILTER = filters.chat(int(OWNER_ID)) & filters.incoming
else:
    OWNER_FILTER = filters.incoming

# Start message
@xbot.on_message(filters.command('start'))
async def start(bot, update):
    await update.reply_photo(photo="https://th.bing.com/th/id/OIG4.iV2l1_HaysKkHZXO8DlJ?pid=ImgGn",caption="𝙄 𝙖𝙢 𝘽𝙪𝙡𝙠𝙇𝙤𝙖𝙙𝙚𝙧\n𝙔𝙤𝙪 𝙘𝙖𝙣 𝙪𝙥𝙡𝙤𝙖𝙙 𝙡𝙞𝙨𝙩 𝙤𝙛 𝙪𝙧𝙡𝙨\n\n/help 𝙛𝙤𝙧 𝙢𝙤𝙧𝙚 𝙙𝙚𝙩𝙖𝙞𝙡𝙨!\n\n #𝙣𝙤𝙩𝙚: 𝙄 𝙖𝙢 𝙊𝙣𝙡𝙮 𝙎𝙪𝙥𝙥𝙤𝙧𝙩 2𝙂𝘽",reply_markup=InlineKeyboardMarkup(START_BUTTONS))


# Helper msg
@xbot.on_message(filters.command('help'))
async def help(bot, update):
    await update.reply_photo(photo="https://th.bing.com/th/id/OIG4.iV2l1_HaysKkHZXO8DlJ?pid=ImgGn",caption="𝙃𝙤𝙬 𝙩𝙤 𝙪𝙨𝙚 𝘽𝙪𝙡𝙠𝙇𝙤𝙖𝙙𝙚𝙧!\n\n2 𝙈𝙚𝙩𝙝𝙤𝙙𝙨:\n- 𝙨𝙚𝙣𝙙 𝙘𝙤𝙢𝙢𝙖𝙣𝙙 /link 𝙖𝙣𝙙 𝙩𝙝𝙚𝙣 𝙨𝙚𝙣𝙙 𝙪𝙧𝙡𝙨, 𝙨𝙚𝙥𝙖𝙧𝙖𝙩𝙚𝙙 𝙗𝙮 𝙣𝙚𝙬 𝙡𝙞𝙣𝙚.\n- 𝙨𝙚𝙣𝙙 𝙩𝙭𝙩 𝙛𝙞𝙡𝙚 (𝙡𝙞𝙣𝙠𝙨), 𝙨𝙚𝙥𝙖𝙧𝙖𝙩𝙚𝙙 𝙗𝙮 𝙣𝙚𝙬 𝙡𝙞𝙣𝙚.\n\n #𝙣𝙤𝙩𝙚: 𝙄 𝙖𝙢 𝙊𝙣𝙡𝙮 𝙎𝙪𝙥𝙥𝙤𝙧𝙩 2𝙂𝘽",reply_markup=InlineKeyboardMarkup(START_BUTTONS))


@xbot.on_message(filters.command('link'))
async def linkloader(bot, update):
    xlink = await update.chat.ask('𝙎𝙚𝙣𝙙 𝙮𝙤𝙪𝙧 𝙡𝙞𝙣𝙠𝙨, 𝙨𝙚𝙥𝙖𝙧𝙖𝙩𝙚𝙙 𝙚𝙖𝙘𝙝 𝙡𝙞𝙣𝙠 𝙗𝙮 𝙣𝙚𝙬 𝙡𝙞𝙣𝙚', filters=filters.text, timeout=300)
    if BUTTONS == True:
        return await xlink.reply('𝙐𝙥𝙡𝙤𝙖𝙙𝙞𝙣𝙜 𝙢𝙚𝙩𝙝𝙤𝙙𝙨.🤖', True, reply_markup=InlineKeyboardMarkup(CB_BUTTONS))
    elif BUTTONS == False:
        pass
    dirs = f'downloads/{update.from_user.id}'
    if not os.path.isdir(dirs):
        os.makedirs(dirs)
    output_filename = str(update.from_user.id)
    filename = f'{dirs}/{output_filename}.zip'
    pablo = await update.reply_text('📥𝑫𝒐𝒘𝒏𝒍𝒐𝒂𝒅𝒊𝒏𝒈 𝒕𝒐 𝒎𝒚 𝒔𝒆𝒓𝒗𝒆𝒓 𝒑𝒍𝒆𝒂𝒔𝒆 𝒘𝒂𝒊𝒕 𝑩𝒂𝒔𝒆𝒅 𝒐𝒏 𝑭𝒊𝒍𝒆 𝑺𝒊𝒛𝒆 𝒊𝒕 𝒘𝒊𝒍𝒍 𝑻𝒂𝒌𝒆 𝑺𝒐𝒎𝒆 𝒕𝒊𝒎𝒆...')
    urlx = xlink.text.split('\n')
    rm, total, up = len(urlx), len(urlx), 0
    await pablo.edit_text(f"🌱Total: {total}\n🪴Downloading: {rm}\n🌳Downloaded: {up}")
    for url in urlx:
        await download_file(url, dirs)
        up+=1
        rm-=1
        try:
            await pablo.edit_text(f"🌱Total: {total}\n🪴Downloading: {rm}\n🌳Downloaded: {up}")
        except BadRequest:
            pass
    await pablo.edit_text('📥𝙐𝙥𝙡𝙤𝙖𝙙𝙞𝙣𝙜 𝙩𝙤 𝙔𝙤𝙪𝙧 𝙩𝙚𝙡𝙚𝙜𝙧𝙖𝙢 𝙘𝙝𝙖𝙩 𝙥𝙡𝙚𝙖𝙨𝙚 𝙬𝙖𝙞𝙩 𝘽𝙖𝙨𝙚𝙙 𝙤𝙣 𝙁𝙞𝙡𝙚 𝙎𝙞𝙯𝙚 𝙞𝙩 𝙬𝙞𝙡𝙡 𝙏𝙖𝙠𝙚 𝙎𝙤𝙢𝙚 𝙩𝙞𝙢𝙚...')
    if AS_ZIP == True:
        shutil.make_archive(output_filename, 'zip', dirs)
        start_time = time.time()
        await update.reply_document(
            filename,
            progress=progress_for_pyrogram,
            progress_args=(
                '📥𝙐𝙥𝙡𝙤𝙖𝙙𝙞𝙣𝙜 𝙩𝙤 𝙔𝙤𝙪𝙧 𝙩𝙚𝙡𝙚𝙜𝙧𝙖𝙢 𝙘𝙝𝙖𝙩 𝙥𝙡𝙚𝙖𝙨𝙚 𝙬𝙖𝙞𝙩 𝘽𝙖𝙨𝙚𝙙 𝙤𝙣 𝙁𝙞𝙡𝙚 𝙎𝙞𝙯𝙚 𝙞𝙩 𝙬𝙞𝙡𝙡 𝙏𝙖𝙠𝙚 𝙎𝙤𝙢𝙚 𝙩𝙞𝙢𝙚...',
                pablo,
                start_time
            )
        )
        await pablo.delete()
        os.remove(filename)
        shutil.rmtree(dirs)
    elif AS_ZIP == False:
        dldirs = [i async for i in absolute_paths(dirs)]
        rm, total, up = len(dldirs), len(dldirs), 0
        await pablo.edit_text(f"🌱Total: {total}\n🪴Downloading: {rm}\n🌳Downloaded: {up}")
        for files in dldirs:
            await send_media(files, pablo)
            up+=1
            rm-=1
            try:
                await pablo.edit_text(f"🌱Total: {total}\n🪴Downloading: {rm}\n🌳Downloaded: {up}")
            except BadRequest:
                pass
            time.sleep(1)
        await pablo.delete()
        shutil.rmtree(dirs)


@xbot.on_message(filters.document & OWNER_FILTER & filters.private)
async def loader(bot, update):
    if BUTTONS == True:
        return await update.reply('𝙔𝙤𝙪 𝙬𝙖𝙣𝙣𝙖 𝙪𝙥𝙡𝙤𝙖𝙙 𝙛𝙞𝙡𝙚𝙨 𝙖𝙨?', True, reply_markup=InlineKeyboardMarkup(CB_BUTTONS))
    elif BUTTONS == False:
        pass
    dirs = f'downloads/{update.from_user.id}'
    if not os.path.isdir(dirs):
        os.makedirs(dirs)
    if not update.document.file_name.endswith('.txt'):
        return
    output_filename = update.document.file_name[:-4]
    filename = f'{dirs}/{output_filename}.zip'
    pablo = await update.reply_text('📥𝑫𝒐𝒘𝒏𝒍𝒐𝒂𝒅𝒊𝒏𝒈 𝒕𝒐 𝒎𝒚 𝒔𝒆𝒓𝒗𝒆𝒓 𝒑𝒍𝒆𝒂𝒔𝒆 𝒘𝒂𝒊𝒕 𝑩𝒂𝒔𝒆𝒅 𝒐𝒏 𝑭𝒊𝒍𝒆 𝑺𝒊𝒛𝒆 𝒊𝒕 𝒘𝒊𝒍𝒍 𝑻𝒂𝒌𝒆 𝑺𝒐𝒎𝒆 𝒕𝒊𝒎𝒆...')
    fl = await update.download()
    with open(fl) as f:
        urls = f.read()
        urlx = urls.split('\n')
        rm, total, up = len(urlx), len(urlx), 0
        await pablo.edit_text(f"🌱Total: {total}\n🪴Downloading: {rm}\n🌳Downloaded: {up}")
        for url in urlx:
            await download_file(url, dirs)
            up+=1
            rm-=1
            try:
                await pablo.edit_text(f"🌱Total: {total}\n🪴Downloading: {rm}\n🌳Downloaded: {up}")
            except BadRequest:
                pass
    await pablo.edit_text('📥𝙐𝙥𝙡𝙤𝙖𝙙𝙞𝙣𝙜 𝙩𝙤 𝙔𝙤𝙪𝙧 𝙩𝙚𝙡𝙚𝙜𝙧𝙖𝙢 𝙘𝙝𝙖𝙩 𝙥𝙡𝙚𝙖𝙨𝙚 𝙬𝙖𝙞𝙩 𝘽𝙖𝙨𝙚𝙙 𝙤𝙣 𝙁𝙞𝙡𝙚 𝙎𝙞𝙯𝙚 𝙞𝙩 𝙬𝙞𝙡𝙡 𝙏𝙖𝙠𝙚 𝙎𝙤𝙢𝙚 𝙩𝙞𝙢𝙚...')
    os.remove(fl)
    if AS_ZIP == True:
        shutil.make_archive(output_filename, 'zip', dirs)
        start_time = time.time()
        await update.reply_document(
            filename,
            progress=progress_for_pyrogram,
            progress_args=(
                '📥𝙐𝙥𝙡𝙤𝙖𝙙𝙞𝙣𝙜 𝙩𝙤 𝙔𝙤𝙪𝙧 𝙩𝙚𝙡𝙚𝙜𝙧𝙖𝙢 𝙘𝙝𝙖𝙩 𝙥𝙡𝙚𝙖𝙨𝙚 𝙬𝙖𝙞𝙩 𝘽𝙖𝙨𝙚𝙙 𝙤𝙣 𝙁𝙞𝙡𝙚 𝙎𝙞𝙯𝙚 𝙞𝙩 𝙬𝙞𝙡𝙡 𝙏𝙖𝙠𝙚 𝙎𝙤𝙢𝙚 𝙩𝙞𝙢𝙚...',
                pablo,
                start_time
            )
        )
        await pablo.delete()
        os.remove(filename)
        shutil.rmtree(dirs)
    elif AS_ZIP == False:
        dldirs = [i async for i in absolute_paths(dirs)]
        rm, total, up = len(dldirs), len(dldirs), 0
        await pablo.edit_text(f"🌱Total: {total}\n🪴Downloading: {rm}\n🌳Downloaded: {up}")
        for files in dldirs:
            await send_media(files, pablo)
            up+=1
            rm-=1
            try:
                await pablo.edit_text(f"🌱Total: {total}\n🪴Downloading: {rm}\n🌳Downloaded: {up}")
            except BadRequest:
                pass
            time.sleep(1)
        await pablo.delete()
        shutil.rmtree(dirs)


@xbot.on_callback_query()
async def callbacks(bot: Client, updatex: CallbackQuery):
    cb_data = updatex.data
    update = updatex.message.reply_to_message
    await updatex.message.delete()
    dirs = f'downloads/{update.from_user.id}'
    if not os.path.isdir(dirs):
        os.makedirs(dirs)
    if update.document:
        output_filename = update.document.file_name[:-4]
        filename = f'{dirs}/{output_filename}.zip'
        pablo = await update.reply_text('📥𝑫𝒐𝒘𝒏𝒍𝒐𝒂𝒅𝒊𝒏𝒈 𝒕𝒐 𝒎𝒚 𝒔𝒆𝒓𝒗𝒆𝒓 𝒑𝒍𝒆𝒂𝒔𝒆 𝒘𝒂𝒊𝒕 𝑩𝒂𝒔𝒆𝒅 𝒐𝒏 𝑭𝒊𝒍𝒆 𝑺𝒊𝒛𝒆 𝒊𝒕 𝒘𝒊𝒍𝒍 𝑻𝒂𝒌𝒆 𝑺𝒐𝒎𝒆 𝒕𝒊𝒎𝒆...')
        fl = await update.download()
        with open(fl) as f:
            urls = f.read()
            urlx = urls.split('\n')
            rm, total, up = len(urlx), len(urlx), 0
            await pablo.edit_text(f"🌱Total: {total}\n🪴Downloading: {rm}\n🌳Downloaded: {up}")
            for url in urlx:
                await download_file(url, dirs)
                up+=1
                rm-=1
                try:
                    await pablo.edit_text(f"🌱Total: {total}\n🪴Downloading: {rm}\n🌳Downloaded: {up}")
                except BadRequest:
                    pass
        os.remove(fl)
    elif update.text:
        output_filename = str(update.from_user.id)
        filename = f'{dirs}/{output_filename}.zip'
        pablo = await update.reply_text('📥Downloading to my server please wait Based on File Size it will Take Some time...')
        urlx = update.text.split('\n')
        rm, total, up = len(urlx), len(urlx), 0
        await pablo.edit_text(f"🌱Total: {total}\n🪴Downloading: {rm}\n🌳Downloaded: {up}")
        for url in urlx:
            await download_file(url, dirs)
            up+=1
            rm-=1
            try:
                await pablo.edit_text(f"🌱Total: {total}\n🪴Downloading: {rm}\n🌳Downloaded: {up}")
            except BadRequest:
                pass
    await pablo.edit_text('📥𝙐𝙥𝙡𝙤𝙖𝙙𝙞𝙣𝙜 𝙩𝙤 𝙔𝙤𝙪𝙧 𝙩𝙚𝙡𝙚𝙜𝙧𝙖𝙢 𝙘𝙝𝙖𝙩 𝙥𝙡𝙚𝙖𝙨𝙚 𝙬𝙖𝙞𝙩 𝘽𝙖𝙨𝙚𝙙 𝙤𝙣 𝙁𝙞𝙡𝙚 𝙎𝙞𝙯𝙚 𝙞𝙩 𝙬𝙞𝙡𝙡 𝙏𝙖𝙠𝙚 𝙎𝙤𝙢𝙚 𝙩𝙞𝙢𝙚...')
    if cb_data == 'zip':
        shutil.make_archive(output_filename, 'zip', dirs)
        start_time = time.time()
        await update.reply_document(
            filename,
            progress=progress_for_pyrogram,
            progress_args=(
                '📥𝙐𝙥𝙡𝙤𝙖𝙙𝙞𝙣𝙜 𝙩𝙤 𝙔𝙤𝙪𝙧 𝙩𝙚𝙡𝙚𝙜𝙧𝙖𝙢 𝙘𝙝𝙖𝙩 𝙥𝙡𝙚𝙖𝙨𝙚 𝙬𝙖𝙞𝙩 𝘽𝙖𝙨𝙚𝙙 𝙤𝙣 𝙁𝙞𝙡𝙚 𝙎𝙞𝙯𝙚 𝙞𝙩 𝙬𝙞𝙡𝙡 𝙏𝙖𝙠𝙚 𝙎𝙤𝙢𝙚 𝙩𝙞𝙢𝙚...',
                pablo,
                start_time
            ), reply_markup=inline_keyboard
        )
        await update.reply_text(message_text)
        await pablo.delete()
        os.remove(filename)
        shutil.rmtree(dirs)
    elif cb_data == '1by1':
        dldirs = [i async for i in absolute_paths(dirs)]
        rm, total, up = len(dldirs), len(dldirs), 0
        await pablo.edit_text(f"🌱Total: {total}\n🪴Downloading: {rm}\n🌳Downloaded: {up}")
        for files in dldirs:
            await send_media(files, pablo,reply_markup=inline_keyboard)
            await update.reply_text(message_text)
            up+=1
            rm-=1
            try:
                await pablo.edit_text(f"🌱Total: {total}\n🪴Downloading: {rm}\n🌳Downloaded: {up}")
            except BadRequest:
                pass
            time.sleep(1)
        await pablo.delete()
        shutil.rmtree(dirs)



xbot.run()
