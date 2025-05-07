clear
cat <<"EOF"
    __  __
   /  |/  (_)_____________  __________
  / /|_/ / / ___/ ___/ __ \/ ___/ ___/
 / /  / / / /  / /  / /_/ / /  / /
/_/  /_/_/_/  /_/   \____/_/  /_/

EOF
echo -e "Loading..."

echo -e "Updating apt-get"
apt-get update

echo -e "Checking and installing Python and dependencies..."

#PYTHON3
if command -v python3 >/dev/null 2>&1; then
    PYTHON_VERSION="$(python3 -V 2>&1 | cut -d' ' -f2)"
    if dpkg --compare-versions $PYTHON_VERSION lt 3.11; then
        echo "Required Python version is 3.11 or higher, please upgrade!"
        exit 1
    else
        echo "Python version $PYTHON_VERSION is installed. Awesome!"
    fi
else
    echo "Python 3 is not installed. Installing..."
    apt install python3 -y
fi

#PYTHON-FLASK
if python3 -c "import flask" &> /dev/null; then
    FLASK_VERSION="$(python3  -c 'import flask; print(flask.__version__)')"
    if dpkg --compare-versions $FLASK_VERSION lt 2.2.2; then
        echo "Required Python Flask version is 2.2.2 or higher, please upgrade!"
        exit 1
    else
        echo "Python Flask version $FLASK_VERSION is installed. Awesome!"
    fi
else
    echo "Python Flask is not installed."
    apt install python3-flask -y
fi

#PYTHON-FLASK-CORS
if python3 -c "import flask_cors" &> /dev/null; then
    FLASK_CORS_VERSION="$(python3  -c 'import flask_cors; print(flask_cors.__version__)')"
    if dpkg --compare-versions $FLASK_CORS_VERSION lt 3.0.10; then
        echo "Required Python Flask CORS version is 3.0.10 or higher, please upgrade!"
        exit 1
    else
        echo "Python Flask CORS version $FLASK_CORS_VERSION is installed. Awesome!"
    fi
else
    echo "Python Flask CORS is not installed."
    apt install python3-flask-cors -y
fi

#PYTHON-YAML
if python3 -c "import yaml" &> /dev/null; then
    YAML_VERSION="$(python3  -c 'import yaml; print(yaml.__version__)')"
    
    if dpkg --compare-versions $YAML_VERSION lt 6.0; then
        echo "Required Python Yaml version is 6.0 or higher, please upgrade!"
        exit 1
    else
        echo "Python Yaml version $YAML_VERSION is installed. Awesome!"
    fi
else
    echo "Python Yaml is not installed."
    apt install python3-yaml -y
fi

echo "Installing app..."
mkdir mirrorr
cd mirrorr
wget -qO main.tar.gz https://api.github.com/repos/mchatzi/mirrorr/tarball --header 'Authorization: token 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'
tar -xzf main.tar.gz
rm main.tar.gz
FOLDER_NAME="$(ls)"
mv $FOLDER_NAME/* .
rm -r $FOLDER_NAME

echo "Starting application..."
setsid python3 web/mirrorr-web.py --log=WARNING &
echo "Started"

#Report to user
IP=$(ip a s dev eth0 | awk '/inet / {print $2}' | cut -d/ -f1)
echo -e "Mirrorr is up!"
echo -e "Web interface: $IP:5000"
