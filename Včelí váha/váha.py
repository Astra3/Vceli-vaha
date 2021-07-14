#!/usr/bin/python3 -u
import logging
import subprocess
import sys
from time import sleep
from typing import List, Union
from os import chdir

from Bluetooth_třída import BluetoothComm
from hx711 import HX711

chdir("/home/pi/Včelí váha")


def bytes_find(inp: bytes, find: Union[bytes, List[bytes]]) -> float:
    for i in find:
        index = inp.find(i)
        if index != -1:
            break
    # noinspection PyUnboundLocalVariable
    return float(inp[index:])


root = logging.getLogger()
root.setLevel(logging.DEBUG)

# Zajistí aby výstup logu šel do stdout a ne do stderr
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s - %(message)s')
handler.setFormatter(formatter)
root.addHandler(handler)

try:
    with open("calibration.txt", "r") as file:
        kalibrace = float(file.readline())
except (ValueError, FileNotFoundError):
    kalibrace = 1


with BluetoothComm() as comm, HX711(9, 11) as vaha:
    comm.send("Inicializace programu...")
    vaha.set_reading_format("MSB", "MSB")
    vaha.set_reference_unit(kalibrace)
    vaha.reset()
    vaha.tare()
    if vaha.get_reference_unit() == 1:
        comm.send("Čtení kalibrace ze souboru bylo neúspěšné, hodnota nastavena na 1.")
    comm.send("Zadejte help pro nápovědu.")
    while True:
        comm.send(f"{vaha.get_weight(5)}")
        read = comm.read
        if b'help' in read:
            comm.send("Nápověda k programu:\n"
                      "power off | vypnout - vypne Raspberry\n"
                      "calibration - vypíše kalibrační faktor váhy\n"
                      "kalibrace - spustí kalibraci váhy\n"
                      "q - vypne program")
        elif b'power off' in read or b'vypnout' in read:
            comm.send("Vypínám systém...")
            logging.info("Vypínám systém...")
            subprocess.run(["poweroff"])
            exit()
        elif b'calibration' in read:
            comm.send(f"Kalibrační faktor: {vaha.get_reference_unit()}")
        elif b"kalibrace" in read:
            comm.send("Připojte se znovu k váze...")
            break
        elif b'q' in read:
            exit()
        vaha.power_down()
        vaha.power_up()
        sleep(.4)

# tahle část kódu se spustí jen pokud se zadá to terminálu "calibrate"
with BluetoothComm(False) as comm, open("calibration.txt", "w") as file:
    comm.send("Zadejte 'enter', pokud si přejete zadat pouze kalibrační hodnotu - cokoliv jiného pro kalibraci")
    if b'enter' in comm.wait_for_input():
        comm.send("Zadejte kalibrační hodnotu")
        try:
            scale = float(comm.wait_for_input())
        except ValueError:
            comm.send("Nelze převést na číslo")
            raise ValueError("Nelze převést na číslo")
        comm.send(f"Kalibrační faktor: {scale}")
    else:
        comm.send("Ujistěte se, že váha je prázdná a pošlete jakoukoliv zprávu pro pokračování")
        comm.wait_for_input()
        with HX711(9, 11) as vaha:
            vaha.set_reading_format("MSB", "MSB")
            vaha.set_reference_unit(1)
            vaha.reset()
            vaha.tare()
            comm.send(f"Nyní položte na váhu nějaký objekt se známou hmotností a tu zadejte...")
            try:
                rel_weight = float(comm.wait_for_input())
            except ValueError:
                comm.send("Nelze převést na číselnou hodnotu!")
                raise ValueError("Hmotnost nelze převést na číselnou hodnotu")

            weight = vaha.get_weight(5)
            scale = weight / rel_weight
            comm.send(f"Kalibrační faktor: {scale}\n"
                      f"{scale} = {weight} / {rel_weight})")
    file.write(str(scale))
    comm.send("Kalibrační faktor uložen, pro pokračovaní se znovu připojte.")
