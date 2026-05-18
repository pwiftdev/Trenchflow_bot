from telegram import Update
from telegram.ext import ContextTypes

from bot.scan_keyboard import DELETE_CALLBACK, REFRESH_PREFIX, build_scan_keyboard
from bot.scan_pipeline import BirdeyeError, BirdeyeTokenNotFound, build_scan_result
from bot.scan_reply import edit_scan_card
from domain.ca import is_valid_solana_address


async def scan_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None or query.data is None:
        return

    if query.data == DELETE_CALLBACK:
        await query.answer()
        if query.message:
            await query.message.delete()
        return

    if not query.data.startswith(REFRESH_PREFIX):
        await query.answer()
        return

    mint = query.data[len(REFRESH_PREFIX) :]
    if not is_valid_solana_address(mint):
        await query.answer("Invalid token address.", show_alert=True)
        return

    try:
        result = await build_scan_result(update, mint)
    except BirdeyeTokenNotFound:
        await query.answer("Token not found on Birdeye.", show_alert=True)
        return
    except BirdeyeError as exc:
        await query.answer(str(exc)[:200], show_alert=True)
        return

    await query.answer()

    if query.message is None:
        return

    await edit_scan_card(
        query.message,
        caption=result.caption,
        keyboard=build_scan_keyboard(result.snapshot),
        snapshot=result.snapshot,
    )
