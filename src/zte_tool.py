from  hashlib import md5, sha256
from datetime import datetime
import json

import requests


class ZTERouter:
    _logged_in = False

    def __init__(self, ip, password):
        self.ip = ip
        self.referer = f"http://{self.ip}/"
        self.password = password
        self.session = requests.Session()

    def hash(self, str):
        return sha256(str.encode()).hexdigest()

    def getVersion(self):
        header = {"Referer": self.referer}
        payload = "isTest=false&cmd=wa_inner_version"
        response = requests.get(
            self.referer + f"goform/goform_get_cmd_process?{payload}",
            headers=header,
            data=payload,
        )
        return response.json()["wa_inner_version"]

    def get_LD(self):
        header = {"Referer": self.referer}
        payload = "isTest=false&cmd=LD"
        response = requests.get(
            self.referer + f"goform/goform_get_cmd_process?{payload}",
            headers=header,
            data=payload,
        )
        return response.json()["LD"].upper()

    def login(self, password=None, LD=None):
        if self._logged_in:
            return self._logged_in
        else:
            password = password or self.password
            LD = LD or self.get_LD()
            header = {"Referer": self.referer}
            hashPassword = self.hash(password).upper()
            ztePass = self.hash(hashPassword + LD).upper()
            payload = "isTest=false&goformId=LOGIN&password=" + ztePass
            response = self.session.post(
                self.referer + "goform/goform_set_cmd_process", headers=header, data=payload
            )
            response.raise_for_status()
            self._logged_in = response.text
            return self._logged_in

    def get_RD(self):
        header = {"Referer": self.referer}
        payload = "isTest=false&cmd=RD"
        response = requests.post(
            self.referer + "goform/goform_get_cmd_process", headers=header, data=payload
        )
        return response.json()["RD"]

    def zteinfo(self):
        self.login()
        ip = self.ip
        cmd_url = f"http://{ip}/goform/goform_get_cmd_process"
        params = {
            "isTest": "false",
            "cmd": ",".join([
                "wa_inner_version", "network_type", "rssi", "rscp", "rmcc", "rmnc", "enodeb_id", "lte_rsrq",
                "lte_rsrp", "Z5g_snr", "Z5g_rsrp", "ZCELLINFO_band", "Z5g_dlEarfcn", "lte_ca_pcell_arfcn",
                "lte_ca_pcell_band", "lte_ca_scell_band", "lte_ca_pcell_bandwidth", "lte_ca_scell_info",
                "lte_ca_scell_bandwidth", "wan_lte_ca", "lte_pci", "Z5g_CELL_ID", "Z5g_SINR", "cell_id",
                "wan_lte_ca", "lte_ca_pcell_band", "lte_ca_pcell_bandwidth", "lte_ca_scell_band",
                "lte_ca_scell_bandwidth", "lte_ca_pcell_arfcn", "lte_ca_scell_arfcn", "lte_multi_ca_scell_info",
                "wan_active_band", "nr5g_pci", "nr5g_action_band", "nr5g_cell_id", "lte_snr", "ecio",
                "wan_active_channel", "nr5g_action_channel", "ngbr_cell_info", "monthly_tx_bytes",
                "monthly_rx_bytes", "lte_pci", "lte_pci_lock", "lte_earfcn_lock", "wan_ipaddr", "wan_apn",
                "pm_sensor_mdm", "pm_modem_5g", "nr5g_pci", "nr5g_action_channel", "nr5g_action_band",
                "Z5g_SINR", "Z5g_rsrp", "wan_active_band", "wan_active_channel", "wan_lte_ca",
                "lte_multi_ca_scell_info", "cell_id", "dns_mode", "prefer_dns_manual", "standby_dns_manual",
                "network_type", "rmcc", "rmnc", "lte_rsrq", "lte_rssi", "lte_rsrp", "lte_snr", "wan_lte_ca",
                "lte_ca_pcell_band", "lte_ca_pcell_bandwidth", "lte_ca_scell_band", "lte_ca_scell_bandwidth",
                "lte_ca_pcell_arfcn", "lte_ca_scell_arfcn", "wan_ipaddr", "static_wan_ipaddr", "opms_wan_mode",
                "opms_wan_auto_mode", "ppp_status", "loginfo&multi_data=1"]),
        }

        headers = {
            "Referer": f"http://{ip}/index.html",
         }

        response = requests.get(cmd_url, headers=headers, params=params)
        return response.json()


    def ztereboot(self):
        self.login()
        version = self.getVersion()
        version_hash = md5(version.encode()).hexdigest()
        rd = self.get_RD()
        ad = md5((version_hash + rd).encode()).hexdigest()
        header = {"Referer": self.referer}
        payload = f"isTest=false&goformId=REBOOT_DEVICE&AD=" + ad
        response = self.session.post(
            self.referer + "goform/goform_set_cmd_process", headers=header, data=payload
        )
        response.raise_for_status()
        return response.text


