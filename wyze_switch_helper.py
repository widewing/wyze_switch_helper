import logging
import subprocess
import requests
import re

logging.basicConfig(level=logging.INFO)


class WyzeSwitchHelper:
    def __init__(self, hass_token):
        self.hass_token = hass_token
        self.device_mapping = self.get_device_mapping()

    def get_device_mapping(self):
        api_endpoint = 'https://hass.wdwg.win/api/states'
        headers = {"Authorization": f'Bearer {self.hass_token}'}
        resp = requests.get(api_endpoint, headers=headers)
        resp.raise_for_status()
        mapping = {
            re.sub('LD_SS1_(.{2})(.{2})(.{2})(.{2})(.{2})(.{2})-switch', r'\1:\2:\3:\4:\5:\6',e["attributes"]["mac"]).lower(): e["entity_id"]
            for e in resp.json()
            if "attributes" in e and "device model" in e["attributes"]
              and e["attributes"]["device model"] == "LD_SS1"
        }
        return mapping

    def update_device(self, mac_address):
        if mac_address not in self.device_mapping:
            logging.error("Unknown device: %s", mac_address)
            return
        entity_id = self.device_mapping[mac_address]
        api_endpoint = 'https://hass.wdwg.win/api/services/homeassistant/update_entity'
        data = {"entity_id": entity_id}
        headers = {"Authorization": f'Bearer {self.hass_token}'}
        try:
            resp = requests.post(api_endpoint, json=data, headers=headers)
            resp.raise_for_status()
            logging.info("Updated entity: %s", entity_id)
        except Exception as e:
            logging.execption(f"An error occurred updating entity %s: %s", entity_id, e)

    def process_tcpdump_output(self):
        # The command to be executed
        mac_filters = " or ".join([f"ether src {m}" for m in self.device_mapping.keys()])
        command = [
            'stdbuf', '-o0', 'tcpdump', '-i', 'br-lan', '-e', '-nn', 
            f'({mac_filters}) and tcp and ip[2:2] - ((ip[0]&0xf)<<2) - ((tcp[12]&0xf0)>>2) > 0'
        ]
        logging.info(" ".join(command))
        
        # Start the tcpdump process
        process = subprocess.Popen(command, stdout=subprocess.PIPE, text=True)
        
        try:
            # Process each line of output in real-time
            for line in process.stdout:
                # Regular expression to extract the source MAC address
                match = re.search(r'(\b[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}\b)', line)
                if match:
                    mac_address = match.group(1)
                    logging.info(f"Found MAC address: {mac_address}")
                    # Call the function to send the MAC address to an API
                    self.update_device(mac_address)
        finally:
            process.terminate()

if __name__ == '__main__':
    wyze_switch_helper = WyzeSwitchHelper(<HASS_TOKEN>)
    wyze_switch_helper.process_tcpdump_output()
