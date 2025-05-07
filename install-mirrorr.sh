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
    PYTHON_VERSION="$(python3 -V 2>&1 | cut -d' ' -f2)"
    if dpkg --compare-versions $PYTHON_VERSION lt 3.12; then
        echo "Required Python version is 3.11 or higher, please upgrade!"
        exit 1
    else
        echo "Python version $PYTHON_VERSION is installed. Awesome!"
    fi
else
    echo "Python 3 is not installed. Installing..."
    #apt install python3 -y
fi

if python3 -c "import flask" &> /dev/null; then
    if dpkg --compare-versions $(python3  -c 'import flask; print(flask.__version__)') lt 2.2.3; then
        echo "Required Python Flask version is 2.2.2 or higher, please upgrade!"
        exit 1
    fi
else
    echo "Flask is not installed."
fi


IP=$(ip a s dev eth0 | awk '/inet / {print $2}' | cut -d/ -f1)


#apt install python -y
#apt install flask -y

#DOING it in mirrorr-web.py now
#mkdir web/logs
#mkdir jobs


#bash -c "setsid python3 web/mirrorr-web.py --log=WARNING"
