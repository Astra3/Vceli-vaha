#!/usr/bin/python3 -u
import logging
import subprocess
import sys
from time import sleep
from typing import List, Union
from os import chdir

from Bluetooth_třída import BluetoothComm
from Měření import Vaha

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

with BluetoothComm() as comm, Vaha(calibration_factor=kalibrace) as vaha:
    if vaha.calibration == 1:
        comm.send("Čtení kalibrace ze souboru bylo neúspěšné.")
    comm.send("Zadejte help pro nápovědu.")
    while True:
        comm.send(f"{vaha.read}")
        read = comm.read
        if b'raw' in read:
            raw = vaha.raw
            comm.send(f"raw hodnota: {raw}")
        elif b'help' in read:
            comm.send("Nápověda k programu:\n"
                      "raw - zobrazí hodnotu tak, jak je hlášená, bez přepočtů\n"
                      "power off | vypnout - vypne Raspberry\n"
                      "calibration - vypíše kalibrační faktor váhy\n"
                      "init read - vypíše init_reading váhy\n"
                      "kalibrace - spustí kalibraci váhy\n"
                      "q - vypne program")
        elif b'power off' in read or b'vypnout' in read:
            comm.send("Vypínám systém...")
            logging.info("Vypínám systém...")
            subprocess.run(["poweroff"])
            exit()
        elif b'calibration' in read:
            comm.send(f"Kalibrační faktor: {vaha.calibration}")
        elif b"init read" in read:
            comm.send(f"Init reading: {vaha.init_reading}")
        elif b"kalibrace" in read:
            comm.send("Připojte se znovu k váze...")
            break
        elif b'q' in read:
            exit()
        sleep(.8)

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
        with Vaha() as vaha:
            comm.send(f"init reading: {vaha.init_reading}\n"
                      f"Nyní položte na váhu nějaký objekt se známou hmotností a tu zadejte...")
            try:
                rel_weight = float(comm.wait_for_input())
            except ValueError:
                comm.send("Nelze převést na číselnou hodnotu!")
                raise ValueError("Hmotnost nelze převést na číselnou hodnotu")

            raw = vaha.raw
            scale = rel_weight / (raw - vaha.init_reading)
            comm.send(f"Kalibrační faktor: {scale}\n"
                      f"{scale} = {rel_weight} / ({raw} - {vaha.init_reading})")
    file.write(str(scale))
    comm.send("Kalibrační faktor uložen, pro pokračovaní se znovu připojte.")
