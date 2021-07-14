import logging
import signal
from threading import Thread
from typing import Union
import bluetooth


class BluetoothComm:
    def __init__(self, read: bool = True):
        """
        Třída pro komunikaci s Bluetooth zařízením vytvořen pomoci tohoto `návodu <https://www.reddit.com/r/raspberry_pi/comments/6nchaj/guide_how_to_establish_bluetooth_serial/?utm_source=share&utm_medium=web2x&context=3>`_
        Příklad použití::
            with BluetoothComm() as comm:
                comm.send("hello")

        :param read: Parametr udávající, zda se má vstup od uživatele zapisovat do proměnné self.read nebo se má vždy čekat při spuštění funkce.
        """
        self._server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        self._server_sock.bind(("", bluetooth.PORT_ANY))
        self._server_sock.listen(1)

        port = self._server_sock.getsockname()[1]
        # bluetooth.advertise_service(self.server_sock, "Včelí váha")

        logging.info(f"Čekám na spojení, port: {port}")
        self.client_sock, address = self._server_sock.accept()
        logging.info(f"Připojeno: {address}")
        self._read: bytes = b''
        signal.signal(signal.SIGINT, self.close)

        if read:
            self._wait = False
            # self._condition = Condition()
            self._thread = Thread(target=self._read_comm, daemon=True)
            self._thread.start()

    def _read_comm(self):
        while True:
            read = self.wait_for_input()
            logging.debug("Do self._read se zapisuje")
            self._read += read
            logging.debug("Do self._read se nezapisuje")

    @property
    def read(self) -> bytes:
        """
        Vrací vstup zadaný do terminálu. Po vybrání vstupu se vymaže.
        Vrací prázdný bytes string, pokud read=False

        :return: bytes string uživatelského vstupu
        """
        a = self._read
        self._read = b''
        return a

    def send(self, text: str, append: bool = True):
        """
        Pošle do Bluetooth terminálu text.

        :param text: text co se pošle do terminálu
        :param append: přidá "\n" na konec textu, pokud tam není
        """
        if append and not text.endswith("\n"):
            text += "\n"
        self.client_sock.send(text)

    def wait_for_input(self) -> Union[bytes, None]:
        """
        Vyčkává, dokud se do terminálu nezadá nějaký vstup.  Nemělo by se používat, pokud bylo read=False při
        inicializaci.

        :return: vrací zadaný input nebo None
        """
        res = self.client_sock.recv(1024)
        if len(res):
            return res
        else:
            logging.debug("do terminálu nebylo nic posláno")
            return None

    def close(self):
        """
        Uzavře connection, aktivuje se automaticky při použití s with
        """
        try:
            self.client_sock.close()
            self._server_sock.close()
        finally:
            logging.info("BluetoothComm ukončen")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
