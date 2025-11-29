import json
import asyncio
import pandas as pd
import typer
import json as js

app = typer.Typer()

HOST = "127.0.0.1"
PORT = 9999

async def send_command(command: dict):
    reader, writer = await asyncio.open_connection(HOST, PORT)
    writer.write(json.dumps(command).encode())
    await writer.drain()
    data = await reader.read(65536)
    writer.close()
    await writer.wait_closed()
    return json.loads(data.decode())

@app.command()
def start(
    bot_name: str = typer.Argument(..., help="Nom unique du bot"),
    bot_type: str = typer.Option("sweep", help="Type de bot à lancer"),
    params_file: str = typer.Option(None, help="Fichier JSON avec paramètres du bot")
):
    """Démarre un bot.
    (venv) xavier@fedora-1:~/Documents/gogs-repository/crypto/bot_skeleton/version_04_event$ /home/xavier/Documents/gogs-repository/crypto/venv/bin/python -m trading_bot.bot_manager.bot_manager_cli start sweep_bot_01 --bot-type sweep_bot --params-file /home/xavier/Documents/gogs-repository/crypto/bot_skeleton/version_04_event/trading_bot/bot_manager/sweep_bot_01.json
    """
    params = {}
    if params_file:
        with open(params_file, "r") as f:
            params = js.load(f)
    command = {"command": "start_bot", "bot_name": bot_name, "bot_type": bot_type, "params": params}
    result = asyncio.run(send_command(command))
    typer.echo(result)

@app.command()
def stop(bot_name: str = typer.Argument(..., help="Nom du bot à arrêter")):
    """Arrête un bot."""
    command = {"command": "stop_bot", "bot_name": bot_name}
    result = asyncio.run(send_command(command))
    typer.echo(result)

@app.command()
def train(
    bot_type: str = typer.Argument(..., help="Type de bot à lancer à Optimiser"),
    params_file: str = typer.Option(None, help="Fichier JSON avec le grid à optimiser")
):
    param_grid = {}
    if params_file:
        with open(params_file, "r") as f:
            param_grid = js.load(f)

    command = {"command": "train_bot", "bot_type": bot_type, "param_grid": param_grid}
    result = asyncio.run(send_command(command))

    # Affichage des stats
    if result:
        results = result.pop("results", None)
        typer.echo(result)

        df = pd.DataFrame(results)
        df = df.sort_values(by="s_normalized_score", ascending=False)
        typer.echo(df)
        # typer.echo("Statistiques : ")
        # typer.echo(" | ".join(f"{k}: {float(v):.4f}" if isinstance(v, float) or hasattr(v, 'item') else f"{k}: {v}" for k, v in stats.items()))
    else:
        typer.echo("Erreur : aucun résultat reçu du serveur.")

@app.command()
def list_bots():
    """Liste tous les bots en cours d’exécution."""
    command = {"command": "list_bots"}
    result = asyncio.run(send_command(command))
    typer.echo(result)

@app.command()
def backtest(
    bot_type: str = typer.Argument(..., help="Type de bot à lancer à Backtester"),
    params_file: str = typer.Option(None, help="Fichier JSON avec paramètres du bot")
):
    params = {}
    if params_file:
        with open(params_file, "r") as f:
            params = js.load(f)

    command = {"command": "backtest_bot", "bot_type": bot_type, "params": params}
    result = asyncio.run(send_command(command))

    # Affichage des stats
    if result:
        stats = result.pop("stats", {})
        typer.echo(result)
        
        df = pd.DataFrame([stats])
        typer.echo(df)
        # typer.echo("Statistiques : ")
        # typer.echo(" | ".join(f"{k}: {float(v):.4f}" if isinstance(v, float) or hasattr(v, 'item') else f"{k}: {v}" for k, v in stats.items()))
    else:
        typer.echo("Erreur : aucun résultat reçu du serveur.")

if __name__ == "__main__":
    app()
