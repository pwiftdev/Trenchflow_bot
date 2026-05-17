from telegram import Update
from telegram.ext import ContextTypes

HELP_TEXT = """<b>Trenchflow</b> — Solana scan bot for trading groups

<b>Scanning</b>
/scan &lt;contract&gt; — Full token card (price, MC, LP, volume, security)
  · Or paste a contract address (DMs always work)
  · In groups: @BotFather → /setprivacy → <b>Disable</b>, then re-add the bot
  · First scan in a group: <b>First call</b> with MC at scan
  · Repeat scan: <b>Since call</b> PnL vs first call in that group

<b>Other</b>
/help — This message

<i>Tip: add the bot as admin so it can post photos in the group.</i>"""


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return
    await update.message.reply_text(HELP_TEXT, parse_mode="HTML")
