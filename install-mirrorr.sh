clear
cat <<"EOF"
    __  __
   /  |/  (_)_____________  __________
  / /|_/ / / ___/ ___/ __ \/ ___/ ___/
 / /  / / / /  / /  / /_/ / /  / /
/_/  /_/_/_/  /_/   \____/_/  /_/

EOF
echo -e "Loading..."
echo -e "Checking and installing dependencies..."

if command -v python3 >/dev/null 2>&1; then
    if dpkg --compare-versions "$(python3 -V 2>&1 | cut -d' ' -f2)" lt 3.11; then
        echo "Required Python version is 3.11 or higher, please upgrade!"
    fi
else
    echo "Python 3 is not installed. Installing..."
    apt install python3 -y
fi


IP=$(ip a s dev eth0 | awk '/inet / {print $2}' | cut -d/ -f1)

#apt install python -y
#apt install flask -y

#DOING it in mirrorr-web.py now
#mkdir web/logs
#mkdir jobs


#bash -c "setsid python3 web/mirrorr-web.py --log=WARNING"
