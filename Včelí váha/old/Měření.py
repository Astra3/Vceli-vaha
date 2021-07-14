from typing import Union

from hx711_gpiozero import HX711
import logging


class Vaha:
    def __init__(self, calibration_factor: int = 1, init_read: int = None, zaokrouhlit: int = 4):
        """
        Třída, která integruje modul HX711 s váhou
        Příklad::
            with Vaha() as vaha:
                print(vaha.read)

        :param calibration_factor:
            Kalibrační faktor získaný ze spuštění tohoto souboru, nesmí být nulový, jinak váha bude číst pořád nulu.
            Tohle číslo upravuje raw hodnoty z váhy na reálnou hmotnost objektu.
        :param init_read:
            Pokud je None, je získána automaticky při zapnutí programu. Jde o číslo určující odchylku váhy při hmotnosti
            0. Třeba pokud váha v nulovém stavu měří 0.08, tak tahle hodnota bude 0.08. **Pokud není hodnota zadaná, je
            třeba při zapnutí programu mít váhu prázdnou!**
        :param zaokrouhlit:
            Určí hodnotu přes funkci round pro zaokrouhlení výstupu.
        """
        self._zaokrouhli = zaokrouhlit
        self._vaha = HX711()
        self.calibration = calibration_factor
        if init_read is None:
            logging.info("_init_reading nebyl zadán")
            self.init_reading = self.raw
        else:
            logging.info("nastavuji _init_reading dle zadání uživatele")
            self.init_reading = init_read
        # self.init_reading = self._round(self.init_reading)
        logging.debug(f"Hodnota init_reading: {self.init_reading}")

        if self.calibration == 0:
            logging.error("Kalibrační faktor na nule způsobuje, že váha bude číst pořád 0")

    @property
    def read(self):
        """
        Současná hodnota váhy s korekcí kalibrace a nulové hodnoty.
        :return: hmotnost objektu
        """
        raw = self.raw
        vaha_value = (raw - self.init_reading) * self.calibration
        # print("raw" + str(self._vaha.raw_value))
        if vaha_value < 0:
            vaha_value = 0.0
        return self._round(vaha_value)

    @property
    def raw(self):
        """
        Čistá hodnota váhy bez jakýchkoliv úprav. Tahle hodnota se neustále mění, je doporučeno si ji uložit do vlastní
        proměnné a poté používat, dokud nebude třeba její obnova.
        :return: hodnota získaná z HX711
        """
        hodnota = self._vaha.value
        return hodnota

    def _round(self, zaokrouhlit: Union[int, float]) -> Union[int, float]:
        """
        Privátní metoda zaokrouhlujíce dle self._zaokrouhli
        :param zaokrouhlit: Číslo ke zaokrouhlení.
        :return: Zaokrouhlená hodnota
        """
        return round(zaokrouhlit, self._zaokrouhli)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._vaha.close()
        logging.info("Váha ukončena")


if __name__ == '__main__':
    if input("Kalibrovat? y/n") == "y":
        from time import sleep
        input("Tento program získá kalibrační faktor váhy.\n"
              "Ujistěte se, že na váze nic není a zmáčkněte enter...")
        vaha = Vaha()
        sleep(.2)
        input("Položte známou hmotnost na váhu a zmáčkněte ENTER.")
        try:
            rel_weight = float(input("Zadejte hmotnost předmětu: "))
        except ValueError as err:
            raise ValueError("Hmotnost může být jen float")
        scale = rel_weight / (vaha.raw - vaha.init_reading)
        print(f"Kalibrační faktor: {scale}\n"
              f"{scale} = {rel_weight} / ({vaha.raw} - {vaha.init_reading})")
    else:
        from time import sleep
        spi = Vaha()
        while True:
            print("return" + str(spi.read))
            sleep(.5)

