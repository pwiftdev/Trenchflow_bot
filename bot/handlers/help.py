from telegram import Update
from telegram.ext import ContextTypes

HELP_TEXT = """<b>Trenchflow</b> — Solana scan bot for trading groups

<b>Scanning</b>
/scan &lt;contract&gt; — Full token card (price, MC, LP, volume, security)
  · First scan in a group: <b>First call</b> with MC at scan
  · Repeat scan: <b>Since call</b> PnL vs first call in that group

You can also paste a Solana contract address (auto-detect coming soon).

<b>Other</b>
/help — This message

<b>Founders / alpha feed</b> (alpha group only)
/founderstest — Test posting to the alpha feed

<i>Tip: add the bot to your group as admin so it can reply to scans.</i>"""


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return
    await update.message.reply_text(HELP_TEXT, parse_mode="HTML")
