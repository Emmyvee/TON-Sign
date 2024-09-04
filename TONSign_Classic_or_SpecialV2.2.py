import os
import glob
import time
from pythonosc.udp_client import SimpleUDPClient

def find_latest_log(directory):
    log_files = glob.glob(os.path.join(directory, "*.txt"))
    if not log_files:
        print("No log files found.")
        return None
    
    latest_log = max(log_files, key=os.path.getmtime)
    print(f"Current VRChat Log: {latest_log}\nRunning! ToN games should appear below! ^^\n===================")
    return latest_log

def classify_round(round_type):
    exempt_rounds = {"Mystic Moon", "Twilight", "Solstice"}
    special_rounds = {"Fog", "Punished", "Sabotage", "Cracked", "Alternate", "Bloodbath", "Midnight", "8 Pages"}
    classic_rounds = {"Classic", "Blood Moon"}
    
    if round_type in exempt_rounds:
        return "Exempt"
    elif round_type in special_rounds:
        return "Special"
    elif round_type in classic_rounds:
        return "Classic"
    else:
        return None

def update_round_log(round_log, round_type):
    classification = classify_round(round_type)
    
    if classification == "Exempt":
        if len(round_log) >= 2:
            if round_log[-2:] == ["Classic", "Classic"]:
                classification = "Special"
            elif round_log[-2:] == ["Classic", "Special"]:
                classification = "Classic"
            elif round_log[-2:] == ["Special", "Classic"]:
                classification = "Special" if is_alternate_pattern(round_log, False) else "Classic"
    
    round_log.append(classification)
    
    if len(round_log) > 7:
        round_log.pop(0)

def is_alternate_pattern(round_log, bonus_flag):
    special_count = sum(1 for round_type in round_log[-6:] if round_type == "Special")
    return special_count > 2 or bonus_flag

def predict_next_round(round_log, bonus_flag):
    if len(round_log) < 2:
        return "Classic"
    
    if round_log[-2:] == ["Special", "Special"]:
        print("The host left before, so removing the last special round.\n===================")
        round_log.pop()

    if is_alternate_pattern(round_log, bonus_flag):
        return "Classic" if round_log[-1] == "Special" else "Special"
    else:
        return "Special" if round_log[-2:] == ["Classic", "Classic"] else "Classic"

def get_recent_rounds_log(round_log):
    return ', '.join(['C' if round_type == "Classic" else 'S' for round_type in round_log])

def monitor_round_types(log_file, known_round_types, osc_client):
    round_log = []
    last_position = 0
    bonus_flag = False

    while True:
        with open(log_file, 'r', encoding='utf-8') as file:
            file.seek(last_position)
            lines = file.readlines()
            new_position = file.tell()

            for line in lines:
                if "BONUS ACTIVE!" in line:  # TERROR NIGHTS STRING
                    bonus_flag = True
                    print("I think it's terror nights! Adjusting!\n.\n.\n.\nok should be good to go now :3\n===================")

                if "OnMasterClientSwitched" in line:
                    print("***\n*** Host just left, next round will be a special.\n***")
                    osc_client.send_message("/avatar/parameters/TON_Sign", True)

                if "Round type is" in line:
                    parts = line.split("Round type is")
                    if len(parts) > 1:
                        possible_round_type = parts[1].strip().split()[0:2]
                        possible_round_type = " ".join(possible_round_type)

                        if possible_round_type in known_round_types:
                            update_round_log(round_log, possible_round_type)
                            print(f"~ New round Started! ~\n~ Round Type: {possible_round_type} ~\n")
                            
                            prediction = predict_next_round(round_log, bonus_flag)
                            special_count = sum(1 for round_type in round_log if round_type == "Special")
                            recent_rounds_log = get_recent_rounds_log(round_log)
                            
                            print(f"(Recent Rounds: {recent_rounds_log})\n ~ Next round SHOULD BE: {prediction}\n===================\nWaiting for the next round... :3")

                            # Send OSC message
                            if prediction == "Special":
                                osc_client.send_message("/avatar/parameters/TON_Sign", True)
                            else:
                                osc_client.send_message("/avatar/parameters/TON_Sign", False)
            
            last_position = new_position

            # Disable the terror nights flag after 6 rounds (assume you have enough data at this point, lol, might still break if it's a new lobby tho sry)
            if len(round_log) >= 6:
                bonus_flag = False

        time.sleep(10)

# OSC setup
ip = "127.0.0.1"
port = 9000
osc_client = SimpleUDPClient(ip, port)

# Current round types in game
round_types = [
    'Classic', 'Fog', 'Punished', 'Sabotage', 'Cracked', 'Alternate',
    'Bloodbath', 'Midnight', 'Mystic Moon', 'Twilight', 'Solstice', 
    '8 Pages', 'Blood Moon'
]

# Directory and file search UPDATED becuase some people's getlogin function EXPLODED so we're doing it this way now :3
log_directory = os.path.join(os.path.expanduser("~"), "AppData", "LocalLow", "VRChat", "VRChat")
latest_log_file = find_latest_log(log_directory)

if latest_log_file:
    monitor_round_types(latest_log_file, round_types, osc_client)
