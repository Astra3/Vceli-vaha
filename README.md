# Včelí váha

Tento projekt slouží k integraci včelí váhy pro Raspberry Pi a modul HX711. Program je rozdělen na třídy, kde třída
BluetoothComm komunikuje s telefonem přes Bluetooth, hx711 je zkopírované [odsud](https://github.com/tatobari/hx711py).
Tento modul je prodloužen ve tříde HX711Update a váha.py pak implementuje oba moduly dohromady a umožňuje komunikace s 
telefonem přes Serial Bluetooth Terminal, a to i včetně kalibrace.