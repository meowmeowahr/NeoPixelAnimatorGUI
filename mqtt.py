from qtpy import QtCore
import paho.mqtt.client as mqtt


class MqttClient(QtCore.QObject):
    Disconnected = 0
    Connecting = 1
    Connected = 2
    ConnectError = 3

    MQTT_3_1 = mqtt.MQTTv31
    MQTT_3_1_1 = mqtt.MQTTv311

    connected = QtCore.Signal()
    disconnected = QtCore.Signal()
    connect_failed = QtCore.Signal()

    stateChanged = QtCore.Signal(int)
    rcChanged = QtCore.Signal(int)
    hostnameChanged = QtCore.Signal(str)
    portChanged = QtCore.Signal(int)
    keepAliveChanged = QtCore.Signal(int)
    cleanSessionChanged = QtCore.Signal(bool)
    protocolVersionChanged = QtCore.Signal(int)

    messageSignal = QtCore.Signal(str, str)

    def __init__(self, parent=None):
        super(MqttClient, self).__init__(parent)

        self.m_hostname = ""
        self.m_port = 1883
        self.m_keepAlive = 60
        self.m_cleanSession = True
        self.m_protocolVersion = MqttClient.MQTT_3_1

        self.m_state = MqttClient.Disconnected
        self.m_result_code = None

        self.m_client = mqtt.Client(clean_session=self.m_cleanSession,
                                    protocol=self.protocolVersion,
                                    callback_api_version=mqtt.CallbackAPIVersion.VERSION1)

        self.m_client.on_connect = self.on_connect
        self.m_client.on_message = self.on_message
        self.m_client.on_disconnect = self.on_disconnect

    @QtCore.Property(int, notify=stateChanged)
    def state(self):
        return self.m_state

    @state.setter
    def state(self, state):
        if self.m_state == state:
            return
        self.m_state = state
        self.stateChanged.emit(state)

    @state.getter
    def state(self):
        return self.m_state

    @QtCore.Property(int, notify=rcChanged)
    def result_code(self):
        return self.m_result_code

    @result_code.setter
    def result_code(self, result_code):
        if self.m_result_code == result_code:
            return
        self.m_result_code = result_code
        self.rcChanged.emit(result_code)

    @result_code.getter
    def result_code(self):
        return self.m_result_code

    @QtCore.Property(str, notify=hostnameChanged)
    def hostname(self):
        return self.m_hostname

    @hostname.setter
    def hostname(self, hostname):
        if self.m_hostname == hostname:
            return
        self.m_hostname = hostname
        self.hostnameChanged.emit(hostname)

    @QtCore.Property(int, notify=portChanged)
    def port(self):
        return self.m_port

    @port.setter
    def port(self, port):
        if self.m_port == port:
            return
        self.m_port = port
        self.portChanged.emit(port)

    @QtCore.Property(int, notify=keepAliveChanged)
    def keepAlive(self):
        return self.m_keepAlive

    @keepAlive.setter
    def keepAlive(self, keepAlive):
        if self.m_keepAlive == keepAlive:
            return
        self.m_keepAlive = keepAlive
        self.keepAliveChanged.emit(keepAlive)

    @QtCore.Property(bool, notify=cleanSessionChanged)
    def cleanSession(self):
        return self.m_cleanSession

    @cleanSession.setter
    def cleanSession(self, cleanSession):
        if self.m_cleanSession == cleanSession:
            return
        self.m_cleanSession = cleanSession
        self.cleanSessionChanged.emit(cleanSession)

    @QtCore.Property(int, notify=protocolVersionChanged)
    def protocolVersion(self):
        return self.m_protocolVersion

    @protocolVersion.setter
    def protocolVersion(self, protocolVersion):
        if self.m_protocolVersion == protocolVersion:
            return
        if protocolVersion in (MqttClient.MQTT_3_1, MqttClient.MQTT_3_1_1):
            self.m_protocolVersion = protocolVersion
            self.protocolVersionChanged.emit(protocolVersion)

    @protocolVersion.getter
    def protocolVersion(self):
        return self.m_protocolVersion

    #################################################################
    @QtCore.Slot()
    def connectToHost(self):
        if self.m_hostname:
            self.m_client.connect_async(self.m_hostname,
                                        port=self.port,
                                        keepalive=self.keepAlive)

            self.state = MqttClient.Connecting
            self.m_client.loop_start()

    @QtCore.Slot()
    def disconnectFromHost(self):
        self.m_client.disconnect()

    def subscribe(self, path):
        if self.state == MqttClient.Connected:
            self.m_client.subscribe(path)

    def publish(self, path, payload):
        if self.state == MqttClient.Connected:
            self.m_client.publish(path, payload)

    #################################################################
    # callbacks
    def on_message(self, mqttc, obj, msg):
        mstr = msg.payload.decode("ascii")
        # print("on_message", mstr, obj, mqttc)
        self.messageSignal.emit(msg.topic, mstr)

    def on_connect(self, client, userdata, flags, rc):
        if rc != 0:
            self.state = MqttClient.ConnectError
            self.m_result_code = rc
            self.connect_failed.emit()
            return
        self.state = MqttClient.Connected
        self.connected.emit()

    def on_disconnect(self, *args):
        # print("on_disconnect", args)
        self.state = MqttClient.Disconnected
        self.disconnected.emit()
