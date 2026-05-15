import structlog

from bot.app import build_application
from config.logging import configure_logging
from config.settings import get_settings


def main() -> None:
    settings = get_settings()
    configure_logging(env=settings.env)
    log = structlog.get_logger()

    application = build_application(settings)

    if settings.env == "dev":
        log.info("starting_bot", env=settings.env, mode="polling")
        application.run_polling(drop_pending_updates=True)
        return

    raise NotImplementedError(
        "Webhook mode is not wired yet. Set ENV=dev for local polling."
    )


if __name__ == "__main__":
    main()
