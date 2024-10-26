from jnius import autoclass, cast
from kivymd.uix.screen import MDScreen

from kivy.logger import Logger
import logging

# Todas as classes java relacionado ao gerenciamento da porta USB no Android
UsbManager = autoclass('android.hardware.usb.UsbManager')
UsbDevice = autoclass('android.hardware.usb.UsbDevice')
UsbDeviceConnection = autoclass('android.hardware.usb.UsbDeviceConnection')
UsbConstants = autoclass('android.hardware.usb.UsbConstants')
Context = autoclass('android.content.Context')
PendingIntent = autoclass('android.app.PendingIntent')
Intent = autoclass('android.content.Intent')
PythonActivity = autoclass('org.kivy.android.PythonActivity')
BroadcastReceiver = autoclass('android.content.BroadcastReceiver')
IntentFilter = autoclass('android.content.IntentFilter')

#Configurar log para depuração
Logger.setLevel(logging.DEBUG)

# Solicitação de permissão do aplicativo ao android para acessar a interface USB
USB_PERMISSION_ACTION = "org.mackenzieapp.mackapptcc.USB_PERMISSION"

class TelaUSB(MDScreen):

    def connect_usb(self):
        # Acessa o gerenciador do USB do android
        activity = PythonActivity.mActivity
        usb_manager = cast(UsbManager, activity.getSystemService(Context.USB_SERVICE))

        # Faz o scan e obtem uma lista de dispositivos conectado a porta USB
        device_list = usb_manager.getDeviceList().values().toArray()  # Obtem a lista
        target_vid = 0x0483  # VID do potenciostato (STMicroeletronics)
        target_pid = 0x5740  # PID

        # Se caso nao houver nenhum dispotivo conectado
        if not device_list:
            self.ids.status_label.text = "No devices found!"
            Logger.debug("TelaUSB: No devices found!")
            return None

        # Caso senha fazer varredura na lista obtida e verificar se é o potenciostato pelo VID e PID como ja mencionado
        for usb_device in device_list:
            vid = usb_device.getVendorId()
            pid = usb_device.getProductId()
            Logger.debug( f"TelaUSB: VID: 0x{vid:02X}, PID: 0x{pid:02X}")
            #Se for o potenciostato ir para verificação de permissão de USB
            if vid == target_vid and pid == target_pid:
                Logger.debug( f"TelaUSB: I caught you ---> VID: 0x{vid:02X}, PID: 0x{pid:02X}")
                self.ids.status_label.text = "Device found!"

                # Verifica se a permissão do dispositivo conectado já existe
                if not self.check_usb_permissions(usb_manager, usb_device):
                    return None  # Aguarde ate a verificação for completa

                # Obtem a interface USB do celular
                interface = usb_device.getInterface(0)

                # Contar o endpoinds do potenciostato conectado na interface USB do celular
                endpoint_count = interface.getEndpointCount()
                Logger.debug( f"TelaUSB: Number of endpoints in interface: {endpoint_count}")

                # Caso nao encontrar nenhum enpoint
                if endpoint_count == 0:
                    self.ids.status_label.text = "No endpoints found in the interface"
                    return None

                # Caso encontrar verificar a direção (IN ou OUT) isso e importante para a troca de dados entre o celular e o potenciostato
                endpoint_out = None
                endpoint_in = None
                #Faz a varredura
                for i in range(endpoint_count):
                    endpoint = interface.getEndpoint(i)
                    #Se o endpoint encontrado estiver na dureçao IN (potenciostato para celular)
                    if endpoint.getDirection() == UsbConstants.USB_DIR_OUT:
                        endpoint_out = endpoint.getAddress()
                        Logger.debug("TelaUSB: USB_DIRECTION: OUT ")
                        Logger.debug( f"TelaUSB: endpoint_out: 0x{endpoint_out}")
                    elif endpoint.getDirection() == UsbConstants.USB_DIR_IN:
                        endpoint_in = endpoint.getAddress()
                        Logger.debug("TelaUSB: USB_DIRECTION: IN ")
                        Logger.debug( f"TelaUSB: endpoint_in: 0x{endpoint_in:02X}")

                #Caso não  consiga encontrar nenhuma direção no endpoint do dispositivo (indicando algum defeito no potenciostato conectado e nao o celular!)
                if not endpoint_out and not endpoint_in:
                    self.ids.status_label.text = "Failed to identify IN/OUT endpoints"
                    Logger.debug( f"TelaUSB: Failed to identify IN/OUT endpoints")
                    return None

                connection = usb_manager.openDevice(usb_device)
                if connection is None:
                    self.ids.status_label.text = "Failed connect the device!"
                    Logger.debug("TelaUSB: Target device not found!")
                    Logger.debug("TelaUSB: Failed connect the device!")
                    return usb_device, interface, None, None, None
                else:
                    Logger.debug("TelaUSB: Setting config communication ...  ")
                    self.config_com()
                    if endpoint_in is None:
                        self.ids.status_label.text = "failure obtain endpoint_in!!"
                        Logger.debug(f"TelaUSB: failure obtain endpoint_in!!, cant procced!!")
                    else:
                        Logger.debug(f"TelaUSB: endpoint_in:0x{endpoint_in:02X}")

                    if endpoint_out is None:
                        self.ids.status_label.text = "failure obtain endpoint_out!!"
                        Logger.debug(f"TelaUSB: failure obtain endpoint_out , cant procced!!")
                    else:
                        Logger.debug(f"TelaUSB: endpoint_out:{endpoint_out:02X}")

                    return usb_device, interface, endpoint_out, endpoint_in, connection

                else:
                    Logger.error(f"TelaUSB: Failure config communication")

                    return usb_device, interface, None, None, None

    def check_usb_permissions(self, usb_manager, usb_device):
        activity = PythonActivity.mActivity

        # Create a pending intent for permission requests
        permission_intent = PendingIntent.getBroadcast(activity, 0, Intent(),PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE)

        # Check if permission has already been granted
        if not usb_manager.hasPermission(usb_device):
            # Request permission if it hasn't been granted
            usb_manager.requestPermission(usb_device, permission_intent)
            self.ids.status_label.text = "Requesting USB permission..."
            Logger.debug("TelaUSB: Requesting USB permission...")
            return False  # Permission is being requested
        Logger.debug("TelaUSB: USB permission granted")
        return True  # Permission is already granted

    def config_com(self):
        pass


    def send_data(self):
        Logger.debug("TelaUSB :Starting send data ...")
        usb_device, interface, endpoint_out, endpoint_in, connection = self.connect_usb()
        Logger.debug( "TelaUSB:  Try sending data ....")
        Logger.debug( f"TelaUSB: usb_device:{usb_device}")
        Logger.debug( f"TelaUSB: interface: {interface}")

        if endpoint_in is None:
            Logger.debug( f"TelaUSB: No have endpoint_in!!")
        else:
            Logger.debug( f"TelaUSB: endpoint_out:{endpoint_in:02X}")

        if endpoint_out is None:
            Logger.debug( f"TelaUSB: No have endpoint_out!!")
        else :
            Logger.debug( f"TelaUSB: endpoint_in:{endpoint_out:02X}")


        if usb_device is None:
            self.ids.data_label.text = "No USB device connected!"
            Logger.debug("TelaUSB: No USB device connected!")
            return

        # Command to send via USB (e.g., 'get' command)
        command = b'get\\n'  # Example command to send
        Logger.debug( f"TelaUSB: command: {command}")

        # Claim the interface
        connection.claimInterface(interface, True)

        # Send data via bulk transfer using the OUT endpoint
        result = connection.bulkTransfer(endpoint_out, command, len(command), 1000)  # Timeout of 1000ms
        Logger.debug( f"TelaUSB: result: {result}")
        if result >= 0:
            self.ids.data_label.text = f"Sent: {command.decode()}"
            Logger.debug( f"Sent: {command.decode()}")
            # Optionally, read the response via the IN endpoint
            #self.receive_data(connection, endpoint_in)
        else:
            self.ids.data_label.text = f"TelaUSB: Failed to send data! Result: {result}"
            Logger.debug( f"TelaUSB: Failed to send data! Result: {result}")
