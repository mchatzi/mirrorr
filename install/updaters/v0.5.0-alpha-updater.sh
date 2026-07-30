#!/bin/bash

echo "This updater will update your Mirrorr to v0.5.0-alpha"

clean_up_js_mess() {
    MESSY_FOLDER="$INSTALLATION_PATH/app/web/frontend"
    for forgotten_file in "index.js" "job.js" "joblog.js" "settings.js"; do
        if [ -f "$MESSY_FOLDER/$forgotten_file" ]; then
            echo "removing leftover: $MESSY_FOLDER/$forgotten_file"
            rm -f "$MESSY_FOLDER/$forgotten_file";
        fi    
    done
}

clean_up_js_mess

