import logging
from queue import Queue
from threading import Thread
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Updater, Filters
import os
import re
from telegram import ParseMode, Bot
import errno

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)
TOKEN = '565882468:AAHsEtAdAM-OukDz87zrhNDYS6p1uA_nDWo'
not_changing_message = '''
به نظر می‌رسد که %s یک فایل زیرنویس نیست.
برای جلوگیری از نابودی فایل‌های غیر زیرنویس این فایل تغییر نخواهد کرد.
'''
BOT_TAG = '\n\nاصلاح زیر نویس فارسی'
USER_TAG = '@farsiSubFixerbot'
USAGE_MSG='فایل زیرنویس خود رو برای ربات بفرستید و فایل اصلاح شده را دانلود کنید.'
fineName = ''
def silentremove(filename):
    try:
        os.remove(filename)
    except OSError as e: # this would be "except OSError, e:" before Python 2.6
        if e.errno != errno.ENOENT: # errno.ENOENT = no such file or directory
            raise # re-raise exception if a different error occurred
class subFix:
    def __init__ (self):
        # args
        global fileName
        #print('\n\nThis is the file\'name :%s',fileName)
        self.fileName = fileName
        
        self.subtitle_fixer = SubtitleFixer()


        with open(self.fileName, 'r') as f:
            lines = f.read()

        lines = self.subtitle_fixer.decode_string(lines)

        silentremove(self.fileName)
        with open(self.fileName, 'w') as f:
            f.write(lines.encode('utf-8'))
        
class SubtitleFixer:
    def __init__(self):
        self.time = '\d\d:\d\d:\d\d,\d\d\d'
        self.number = u'۰۱۲۳۴۵۶۷۸۹'

        self.string = ''

    def fix_encoding(self):
        assert isinstance(self.string, str), repr(self.string)
        #if isinstance(self.string, unicode):
            #return 'utf8'

        try:
            self.string.decode('utf8', 'strict')
            self.string = self.string.decode('utf8')
            return 'utf8'
        except UnicodeError:
            pass

        try:
            self.string.decode('utf16', 'strict')
            self.string = self.string.decode('utf16')
            return 'utf16'
        except UnicodeError:
            pass

        self.string = self.string.decode('windows-1256')
        return 'windows-1256'

    def fix_italic(self):
        self.string = self.string.replace('<i>' , '')
        self.string = self.string.replace('</i>', '')

    def fix_arabic(self):
        self.string = self.string.replace(u'ي', u'ی')
        self.string = self.string.replace(u'ك', u'ک')

    def fix_question_mark(self):
        # quistion mark in persina is ؟ not ?
        self.string = self.string.replace('?', u'؟')

    def fix_other(self):
        self.string = self.string.replace(u'\u202B', u'')

        lines  = self.string.split('\n')
        string = ''

        for line in lines:
            if re.match('^%s\s-->\s%s$' % (self.time, self.time), line):
                string += line
            elif re.match('^%s\s-->\s%s$' % (self.time, self.time), line[:-1]):
                string += line
            elif line.strip() == '':
                string += line
            elif re.match('^\d+$', line):
                string += line
            elif re.match('^\d+$', line[:-1]):
                string += line
            else:
                # this should be subtitle
                s = re.match('^([\.!?]*)', line)

                try:
                    line = re.sub('^%s' % s.group(), '', line)
                except:
                    pass

                # use persian numbers
                for i in range(0, 10):
                    line = line.replace(str(i), self.number[i])

                # for ltr problems some peoples put '-' on EOL
                # it should be in start
                if len(line) != 0 and line[-1] == '-':
                    line = '- %s' % line[:-1]
                line += s.group()

                # put rtl char in start of line (it forces some player to show that line rtl
                string += u'\u202B' + unicode(line)

            # noting to see here
            string += '\n'

            self.string = string


    def decode_string(self, string):
        self.string = string

        self.fix_encoding()

        self.fix_italic()
        self.fix_arabic()
        self.fix_question_mark()
        self.fix_other()

        return self.string


# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.
def start(bot, update):
    """Send a message when the command /start is issued."""
    update.message.reply_text(USAGE_MSG)


def help(bot, update):
    """Send a message when the command /help is issued."""
    update.message.reply_text(USAGE_MSG)
    
def fix(bot, update):
    try:
        
        #print(update.message.document.file_id)
        fileId=update.message.document.file_id
        global fileName
        fileName=update.message.document.file_name
        print(fileName)
        newFile = bot.get_file(fileId)
        newFile.download(fileName)
        subFix()
        #print('done')
        #print(fileName)
        #fileName='amd.srt'
        temp=fileName.encode('ascii','ignore')
        update.message.reply_document(document=open(temp, 'rb'),caption=BOT_TAG+'\n'+USER_TAG,parse_mode=ParseMode.MARKDOWN)
        #bot.send_document(update.message.chat_id,document=open('asf.srt', 'rb'))
        silentremove(fileName)
    except(IndexError, ValueError):
        logger.warning('Update "%s" caused error "%s"', update,error)

def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)

# Write your handlers here


def setup(webhook_url=None):
    """If webhook_url is not passed, run with long-polling."""
    logging.basicConfig(level=logging.WARNING)
    if webhook_url:
        bot = Bot(TOKEN)
        update_queue = Queue()
        dp = Dispatcher(bot, update_queue)
    else:
        updater = Updater(TOKEN)
        bot = updater.bot
        dp = updater.dispatcher
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(CommandHandler("help", help))

        # on noncommand i.e message - echo the message on Telegram
        dp.add_handler(MessageHandler(Filters.document, fix))

        # log all errors
        dp.add_error_handler(error)
    # Add your handlers here
    if webhook_url:
        bot.set_webhook(webhook_url=webhook_url)
        thread = Thread(target=dp.start, name='dispatcher')
        thread.start()
        return update_queue, bot
    else:
        bot.set_webhook()  # Delete webhook
        updater.start_polling()
        updater.idle()


if __name__ == '__main__':
    setup()
