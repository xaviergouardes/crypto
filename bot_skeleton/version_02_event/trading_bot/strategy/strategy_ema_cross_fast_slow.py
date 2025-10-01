from datetime import datetime

from collections import deque
from trading_bot.core.event_bus import EventBus
from trading_bot.core.events import TradeSignalGenerated, IndicatorUpdated, PriceUpdated,CandleClose

class MovingAverageBuffer:
    """Collecte des valeurs d'EMA rapide et lente pour détecter des croisements fiables."""

    def __init__(self):
        self.slow_ma_buffer = deque(maxlen=3)
        self.fast_ma_buffer = deque(maxlen=3)

    def addFast(self, value: float):
        self.fast_ma_buffer.append(value)

    def addSlow(self, value: float):
        self.slow_ma_buffer.append(value)

    def is_ready(self) -> bool:
        """Vérifie si les deux buffers ont bien 3 valeurs."""
        return (len(self.fast_ma_buffer) == 3) and (len(self.slow_ma_buffer) == 3)

    def get_slope(self, buffer: deque) -> float:
        """
        Calcule la pente moyenne sur les 3 dernières valeurs.
        Plus la valeur est grande, plus la tendance est forte.
        """
        if len(buffer) < 3:
            return 0.0
        
        # Pente = variation moyenne entre les points successifs
        return (buffer[-1] - buffer[0]) / 2

    def show(self):
        """Affiche le contenu des buffers de manière lisible."""
        print("\n📊 État actuel du buffer EMA")
        print("─────────────────────────────")
        print(f"📈 EMA rapide ({len(self.fast_ma_buffer)}/3) : {list(self.fast_ma_buffer)}")
        print(f"   ➤ Pente rapide : {self.get_slope(self.fast_ma_buffer):.6f}")
        print(f"🐢 EMA lente  ({len(self.slow_ma_buffer)}/3) : {list(self.slow_ma_buffer)}")
        print(f"   ➤ Pente lente  : {self.get_slope(self.slow_ma_buffer):.6f}")
        print("─────────────────────────────\n")

    def is_crossing(self, slope_threshold: float = 0.0):
        """
        Détecte s'il y a un croisement EMA rapide / EMA lente.
        Retourne 'bullish', 'bearish' ou None.
        
        slope_threshold : pente minimale absolue de l'EMA rapide pour valider le signal.
                          Exemple : 0.0001 (à ajuster selon l'unité de tes prix)
        """
        if not self.is_ready():
            print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [StrategyEmaCandleSlopeEngine] ⚠️ Impossible de détecter un croisement - Initialisation en cours")
            return None

        # Extraire les 2 dernières valeurs pour vérifier le croisement
        fast_prev = self.fast_ma_buffer[-2]
        fast_curr = self.fast_ma_buffer[-1]
        slow_prev = self.slow_ma_buffer[-2]
        slow_curr = self.slow_ma_buffer[-1]

        # Différences avant / après
        prev_diff = fast_prev - slow_prev
        curr_diff = fast_curr - slow_curr

        # Calculer les pentes
        fast_slope = self.get_slope(self.fast_ma_buffer)
        slow_slope = self.get_slope(self.slow_ma_buffer)

        # Debug (facultatif)
        # print(f"Fast slope: {fast_slope:.5f}, Slow slope: {slow_slope:.5f}")

        # ✅ Filtrage : on ne considère un signal que si la pente rapide est suffisante
        if abs(fast_slope) < slope_threshold:
            return None

        # ✅ Optionnel : on peut aussi exiger que les deux pentes aillent dans le même sens
        # (décommente si tu veux encore plus filtrer)
        if (fast_slope > 0 and slow_slope < 0) or (fast_slope < 0 and slow_slope > 0):
            return None

        # ✅ Détection de croisement
        if prev_diff < 0 and curr_diff > 0 and fast_slope > 0:
            return "bullish"   # 📈 Croisement haussier confirmé
        elif prev_diff > 0 and curr_diff < 0 and fast_slope < 0:
            return "bearish"   # 📉 Croisement baissier confirmé
        else:
            return None  # Aucun croisement fiable


class StrategyEmaCrossFastSlowEngine:
    """
    Stratégie : génère des signaux selon le croisement entre une EM lente et une EM rapide
    """

    def __init__(self, event_bus: EventBus, periode_slow_ema: int = 25, periode_fast_ema: int = 9, slope_threshold = 0.01):
        self.event_bus = event_bus

        self.slope_threshold = slope_threshold
        self.periode_slow_ema = periode_slow_ema
        self.periode_fast_ema = periode_fast_ema
        self.entry_price = None
        self.state = "initializing"
        self.moving_buffer = MovingAverageBuffer()
        self.current_candle = None

        # Flags pour savoir si on a reçu au moins un événement de chaque type
        # self.received_indicator = False
        # self.received_price = False

        # Abonnement aux SMA des chandelles
        self.event_bus.subscribe(IndicatorUpdated, self.on_indicator_update)
        self.event_bus.subscribe(PriceUpdated, self.on_price_update)

        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [StrategyEmaCrossFastSlowEngine] Initisation - periode_slow_ema={self.periode_slow_ema} / periode_fast_ema={self.periode_fast_ema} / slope_threshold={self.slope_threshold}  ") 

    async def on_candle_close(self, event: CandleClose):
        self.current_candle = event.candle

    async def on_price_update(self, event: PriceUpdated) -> None:
        """Réception d'un nouveau prix."""
        self.entry_price = event.price

    async def on_indicator_update(self, event: IndicatorUpdated):
        
        # Alimentation du Buffer avec 3 valeurs
        period = event.values.get("ema_candle_period")
        value = event.values.get("ema_candle")
        if period is None or value is None:
            return
        
        if int(period) == self.periode_slow_ema:
            self.moving_buffer.addSlow(float(value))

        if int(period) == self.periode_fast_ema:
            self.moving_buffer.addFast(float(value))      

        if not self.moving_buffer.is_ready():
            return

        # self.received_indicator = True
        await self.evaluate_strategy()


    async def evaluate_strategy(self):
        # print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [StrategyEmaCrossFastSlowEngine] Evaluer la stratégie")
        # self.moving_buffer.show()

        # On ne calcule un signal que si tous les deux  événements ont été reçus au moins une fois
        # if not (self.received_indicator and self.received_price):
        #     print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [StrategyEmaCrossFastSlowEngine] Pas assez de données pour évaluer la stratégie")
        #     print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [StrategyEmaCrossFastSlowEngine] self.received_indicator = {self.received_indicator} / self.received_price={self.received_price}")
        #     return

        if self.entry_price is None or self.on_candle_close is None:
            return

        o, c = self.candle['open'], self.candle['close']
        h, l = self.candle['high'], self.candle['low']
        # c1, c2 = data[t-1]['close'], data[t-2]['close']
        # e, e1, e2 = ema[t], ema[t-1], ema[t-2]

        crossing = self.moving_buffer.is_crossing(slope_threshold=self.slope_threshold)
        if crossing == "bullish":
            signal = "BUY"
        elif crossing == "bearish":
            signal = "SELL"
        else :
            signal = None
        # print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [StrategyEmaCrossFastSlowEngine] crossing={crossing} / signal={signal} / entry_price={self.entry_price}")
    
        if signal:
            await self.event_bus.publish(TradeSignalGenerated(
                side=signal,
                confidence=1.0,
                price=self.entry_price,  
            ))

        # self.received_indicator = False
        # self.received_price = False

    async def run(self):
        """Rien à faire ici : tout est événementiel."""
        pass
