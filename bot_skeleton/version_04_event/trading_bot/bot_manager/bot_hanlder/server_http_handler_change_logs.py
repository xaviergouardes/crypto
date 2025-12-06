from aiohttp import web

from trading_bot.core.logger import Logger

class HttpServerChangeLogs():

    _logger = Logger.get("HttpServerChangeLogs")

    async def execute(self, request):
        try:
            data = await request.json()
            logger_name = data.get("logger")      # ex: "Backtest", "TradeJournal", "Bot.sweep_bot_01"
            level       = data.get("level")       # ex: "DEBUG", "INFO", "WARN", "ERROR"

            if not logger_name or not level:
                return web.json_response(
                    {"error": "Fields 'logger' and 'level' are required"},
                    status=400
                )

            # Si ALL → changer tous les loggers
            if logger_name.upper() == "ALL":
                ok = Logger.change_all_levels(level)
                if not ok:
                    return web.json_response({"error": "Invalid level"}, status=400)

                return web.json_response({
                    "status": "ok",
                    "logger": "ALL",
                    "new_level": level
                })
        

            ok = Logger.change_level(logger_name, level)

            if not ok:
                return web.json_response({"error": "Unknown logger or invalid level"}, status=404)

            return web.json_response({
                "status": "ok",
                "logger": logger_name,
                "new_level": level
            })

        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)