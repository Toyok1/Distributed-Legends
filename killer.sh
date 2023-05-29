kill $(ps aux | grep 'lobby.py' | awk '{print $2}') &
kill $(ps aux | grep 'clientController.py' | awk '{print $2}') &
kill $(ps aux | grep 'client.py' | awk '{print $2}') &
kill $(ps aux | grep 'client.py' | awk '{print $2}')