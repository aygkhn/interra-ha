"""Interra entegrasyonu sabitleri."""
DOMAIN = "interra"

CONF_HOST = "host"
CONF_PORT = "port"
CONF_LOCAL_HOST = "local_host"
CONF_LOCAL_PORT = "local_port"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"

DEFAULT_PORT = 2083

# Interra nesne tipleri (objectType)
OBJ_LIGHT = 1
OBJ_CURTAIN = 2
OBJ_BLIND = 3
OBJ_AC = 4
OBJ_GENERAL = 5
OBJ_ALARM = 7
OBJ_CAM = 27
SHOWN_TYPES = {OBJ_LIGHT, OBJ_CURTAIN, OBJ_BLIND, OBJ_AC, OBJ_GENERAL, OBJ_ALARM, OBJ_CAM}
COVER_TYPES = {OBJ_CURTAIN, OBJ_BLIND}

# Aksiyon tipleri (DeviceActionType)
ACT_OPEN = 1
ACT_CLOSE = 2
ACT_VALUE = 4
ACT_UP = 14
ACT_DOWN = 15
ACT_STOP = 16

# requestType
REQ_DB = 13
REQ_DEVICE = 14
REQ_STATUS = 20
REQ_REGISTER = 19
REQ_LOGIN = 500

# objectType -> abonelik (SubscriptionFlags) id
OT_TO_FLAG = {1: 1, 2: 3, 3: 2, 4: 6, 5: 17, 7: 5, 27: 1}

# Değer/yüzde yeteneği bu özniteliklerden anlaşılır
VALUE_KEYS = {"MaxValue", "MinValue", "ValueType", "SendValueStep"}

ACK_INTERVAL = 200  # sn

SIGNAL_UPDATE = "interra_update_{}"       # cihaz id'si ile biçimlenir
SIGNAL_CONN = "interra_connection"        # bağlantı durumu
