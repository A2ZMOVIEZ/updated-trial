import random
import string
from threading import Thread
from telegram.ext import CommandHandler
from telegram import InlineKeyboardMarkup, ParseMode, InlineKeyboardButton
from bot.helper.mirror_utils.upload_utils.gdriveTools import GoogleDriveHelper
from bot.helper.telegram_helper.message_utils import *
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.mirror_utils.status_utils.clone_status import CloneStatus
from bot import dispatcher, LOGGER, CLONE_LIMIT, STOP_DUPLICATE, download_dict, download_dict_lock, Interval, MIRROR_LOGS, BOT_PM, CHANNEL_USERNAME, bot, FSUB_CHANNEL_ID, FSUB, AUTO_DELETE_UPLOAD_MESSAGE_DURATION
from bot.helper.ext_utils.bot_utils import get_readable_file_size, is_gdrive_link, is_gdtot_link, is_appdrive_link, new_thread
from bot.helper.mirror_utils.download_utils.direct_link_generator import gdtot, appdrive
from bot.helper.ext_utils.exceptions import DirectDownloadLinkException

@new_thread
def cloneNode(update, context):
    if AUTO_DELETE_UPLOAD_MESSAGE_DURATION != -1:
        reply_to =update.message.reply_to_message
        if reply_to is not None:
            reply_to.delete()
    if FSUB:
        try:
            uname = f'<a href="tg://user?id={update.message.from_user.id}">{update.message.from_user.first_name}</a>'
            user = bot.get_chat_member(f"{FSUB_CHANNEL_ID}", update.message.from_user.id)
            LOGGER.error(user.status)
            if user.status not in ('member', 'creator', 'administrator'):
                buttons = ButtonMaker()
                buttons.buildbutton("Click Here To Join Updates Channel", f"https://t.me/{CHANNEL_USERNAME}")
                reply_markup = InlineKeyboardMarkup(buttons.build_menu(1))
                message = sendMarkup(str(f"️<b>Dear {uname}, You haven't join our Updates Channel yet.</b>\n\nKindly Join @{CHANNEL_USERNAME} To Use Bots. "), bot, update, reply_markup)
                Thread(target=auto_delete_upload_message, args=(bot, update.message, message)).start()
                return
        except Exception as error:
            LOGGER.warning(error)
            pass
    if BOT_PM:
        try:
            msg1 = f'𝙰𝙳𝙳𝙴𝙳 𝚈𝙾𝚄𝚁 𝚁𝙴𝚀𝚄𝙴𝚂𝚃𝙴𝙳 𝙻𝙸𝙽𝙺 𝚃𝙾 𝙲𝙻𝙾𝙽𝙴\n'
            send = bot.sendMessage(update.message.from_user.id, text=msg1,)
            send.delete()
        except Exception as e:
            LOGGER.warning(e)
            bot_d = bot.get_me()
            b_uname = bot_d.username
            uname = f'<a href="tg://user?id={update.message.from_user.id}">{update.message.from_user.first_name}</a>'
            channel = CHANNEL_USERNAME
            botstart = f"http://t.me/{b_uname}"
            keyboard = [
                [InlineKeyboardButton("𝚂𝚃𝙰𝚁𝚃 𝙼𝙴", url=f"{botstart}")],
                [InlineKeyboardButton("𝙹𝙾𝙸𝙽 𝙷𝙴𝚁𝙴 𝚃𝙾 𝚄𝚂𝙴 𝙼𝙴", url=f"t.me/{channel}")]]
            message = sendMarkup(
                f"Dear {uname},\n\n<b>𝙸 𝙵𝙾𝚄𝙽𝙳 𝚃𝙷𝙰𝚃 𝚈𝙾𝚄 𝙷𝙰𝚅𝙴𝙽'𝚃 𝚂𝚃𝙰𝚁𝚃𝙴𝙳 𝙼𝙴 𝙸𝙽 𝙿𝙼(Private Chat) 𝚈𝙴𝚃.</b>\n\n𝙵𝚁𝙾𝙼 𝙽𝙾𝚆 𝙾𝙽 𝙸 𝚆𝙸𝙻𝙻 𝙶𝙸𝚅𝙴 𝙻𝙸𝙽𝙺 & 𝙻𝙴𝙴𝙲𝙷𝙴𝙳 𝙵𝙸𝙻𝙴𝚂 𝙸𝙽 𝙿𝙼 & 𝙻𝙾𝙶 𝙲𝙷𝙰𝙽𝙽𝙴𝙻 𝙾𝙽𝙻𝚈.",
                bot, update, reply_markup=InlineKeyboardMarkup(keyboard))
            Thread(target=auto_delete_message, args=(bot, update.message, message)).start()
            return
    args = update.message.text.split(" ", maxsplit=1)
    reply_to = update.message.reply_to_message
    link = ''
    if len(args) > 1:
        link = args[1]
        if update.message.from_user.username:
            tag = f"@{update.message.from_user.username}"
        else:
            tag = update.message.from_user.mention_html(update.message.from_user.first_name)
    elif reply_to is not None:
        if len(link) == 0:
            link = reply_to.text
        if reply_to.from_user.username:
            tag = f"@{reply_to.from_user.username}"
        else:
            tag = reply_to.from_user.mention_html(reply_to.from_user.first_name)
    is_gdtot = is_gdtot_link(link)
    is_appdrive = is_appdrive_link(link)
    if is_gdtot:
        msg = sendMessage(f"Processing: <code>{link}</code>", context.bot, update)
        try:
            link = gdtot(link)
            deleteMessage(context.bot, msg)
        except DirectDownloadLinkException as e:
            deleteMessage(context.bot, msg)
            return sendMessage(str(e), context.bot, update)
    elif is_appdrive:
        msg = sendMessage(f"Processing: <code>{link}</code>", context.bot, update)
        try:
            apdict = appdrive(link)
            link = apdict.get('gdrive_link')
            deleteMessage(context.bot, msg)
        except DirectDownloadLinkException as e:
            deleteMessage(context.bot, msg)
            return sendMessage(str(e), context.bot, update)
    if is_gdrive_link(link):
        gd = GoogleDriveHelper()
        res, size, name, files = gd.helper(link)
        if res != "":
            return sendMessage(res, context.bot, update)
        if STOP_DUPLICATE:
            LOGGER.info('Checking File/Folder if already in Drive...')
            smsg, button = gd.drive_list(name, True, True)
            if smsg:
                msg3 = "File/Folder is already available in Drive.\nHere are the search results:"
                return sendMarkup(msg3, context.bot, update, button)
        if CLONE_LIMIT is not None:
            LOGGER.info('Checking File/Folder Size...')
            if size > CLONE_LIMIT * 1024**3:
                msg2 = f'Failed, Clone limit is {CLONE_LIMIT}GB.\nYour File/Folder size is {get_readable_file_size(size)}.'
                return sendMessage(msg2, context.bot, update)
        if files <= 20:
            msg = sendMessage(f"Cloning: <code>{link}</code>", context.bot, update)
            result, button = gd.clone(link)
            deleteMessage(context.bot, msg)
        else:
            drive = GoogleDriveHelper(name)
            gid = ''.join(random.SystemRandom().choices(string.ascii_letters + string.digits, k=12))
            clone_status = CloneStatus(drive, size, update, gid)
            with download_dict_lock:
                download_dict[update.message.message_id] = clone_status
            sendStatusMessage(update, context.bot)
            result, button = drive.clone(link)
            with download_dict_lock:
                del download_dict[update.message.message_id]
                count = len(download_dict)
            try:
                if count == 0:
                    Interval[0].cancel()
                    del Interval[0]
                    delete_all_messages()
                else:
                    update_all_messages()
            except IndexError:
                pass
        cc = f'\n\n<b>#Ꮯʟᴏɴᴇᴅ Ᏼʏ: </b>{tag}'
        if button in ["cancelled", ""]:
            sendMessage(f"{tag} {result}", context.bot, update)
        else:
            if AUTO_DELETE_UPLOAD_MESSAGE_DURATION != -1:
                auto_delete_message = int(AUTO_DELETE_UPLOAD_MESSAGE_DURATION / 60)
                if update.message.chat.type == 'private':
                    warnmsg = ''
                else:
                    warnmsg = f'\n<b>𝚃𝙷𝙸𝚂 𝙼𝙴𝚂𝚂𝙰𝙶𝙴 𝚆𝙸𝙻𝙻 𝙱𝙴 𝙳𝙴𝙻𝙴𝚃𝙴𝙳 𝙸𝙽 <i>{auto_delete_message} 𝙼𝙸𝙽𝚄𝚃𝙴𝚂</i> 𝙵𝚁𝙾𝙼 𝚃𝙷𝙸𝚂 𝙶𝚁𝙾𝚄𝙿.</b>\n'
        if BOT_PM and update.message.chat.type != 'private':
            pmwarn = f"\n<b>𝙸 𝙷𝙰𝚅𝙴 𝚂𝙴𝙽𝚃 𝙻𝙸𝙽𝙺𝚂 𝙸𝙽 𝙿𝙼.</b>\n"
        elif update.message.chat.type == 'private':
            pmwarn = ''
        else:
            pmwarn = ''
        uploadmsg = sendMarkup(result + cc + pmwarn + warnmsg, context.bot, update, button)
        Thread(target=auto_delete_upload_message, args=(bot, update.message, uploadmsg)).start()
        if is_gdtot:
            gd.deletefile(link)
        elif is_appdrive:
            if apdict.get('link_type') == 'login':
                LOGGER.info(f"Deleting: {link}")
                gd.deleteFile(link)
        if MIRROR_LOGS:
            try:
                for i in MIRROR_LOGS:
                    bot.sendMessage(chat_id=i, text=result + cc, reply_markup=button, parse_mode=ParseMode.HTML)
            except Exception as e:
                LOGGER.warning(e)
            if BOT_PM and update.message.chat.type != 'private':
                try:
                    bot.sendMessage(update.message.from_user.id, text=result, reply_markup=button, parse_mode=ParseMode.HTML)
                except Exception as e:
                    LOGGER.warning(e)
                    return
    else:
        message = sendMessage('Send Gdrive or gdtot link along with command or by replying to the link by command',
                              context.bot, update)
        Thread(target=auto_delete_message, args=(bot, update.message, message)).start()

clone_handler = CommandHandler(BotCommands.CloneCommand, cloneNode, filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
dispatcher.add_handler(clone_handler)
