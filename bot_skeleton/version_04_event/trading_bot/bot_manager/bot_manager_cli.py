import json
import asyncio
import typer

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
    """Démarre un bot."""
    import json as js
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
def train(bot_name: str = typer.Argument(..., help="Nom du bot à entraîner")):
    """Entraîne un bot déjà lancé."""
    command = {"command": "train_bot", "bot_name": bot_name}
    result = asyncio.run(send_command(command))
    typer.echo(result)

@app.command()
def list_bots():
    """Liste tous les bots en cours d’exécution."""
    command = {"command": "list_bots"}
    result = asyncio.run(send_command(command))
    typer.echo(result)

@app.command()
def backtest(bot_name: str):

    command = {"command": "backtest_bot", "bot_name": bot_name}
    result = asyncio.run(send_command(command))

    # Affichage des stats
    if result:
        stats = result.get("stats", {})
        typer.echo(f"\nBacktest de {bot_name} terminé :")
        typer.echo(f"  → Win Rate    : {stats.get('win_rate', 0):.2f}%")
        typer.echo(f"  → Nb Trades   : {stats.get('total_trades', 0)}")
        typer.echo(f"  → Total Pnl   : {stats.get('total_pnl', 0):.2f}")
        typer.echo(f"  → Min Pnl     : {stats.get('pnl_min', 0):.3f}")
        typer.echo(f"  → Max Pnl     : {stats.get('pnl_max', 0):.3f}")
    else:
        typer.echo("Erreur : aucun résultat reçu du serveur.")

if __name__ == "__main__":
    app()
