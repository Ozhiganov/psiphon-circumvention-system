#!/bin/bash

# Copyright (c) 2012, Psiphon Inc.
# All rights reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

NORMAL_USER=ubuntu
MAIL_USER=mail_responder
MAIL_HOME=/home/mail_responder

grep '!!!' settings.py > /dev/null
if [ "$?" -ne "1" ]; then
    echo "You must edit settings.py before attempting to install"
    exit 1
fi

# Put the source files where they need to be. 
echo "Copying source files..."

# Copy the simple files
sudo cp settings.py mail_process.py sendmail.py blacklist.py mail_stats.py \
        mail_direct.py postfix_queue_check.pl log_processor.py $MAIL_HOME

# forward needs to be copied to .forward
sudo cp forward $MAIL_HOME/.forward

# Fix ownership of the files
sudo chown mail_responder:mail_responder $MAIL_HOME/* $MAIL_HOME/.forward

# Make the files readable by anyone (e.g., other users will use them for cron jobs)
sudo chmod a+r  $MAIL_HOME/* $MAIL_HOME/.forward

# Make log_processor.py executable by anyone (e.g., by rsyslog)
sudo chmod a+x  $MAIL_HOME/log_processor.py

# Nuke the compiled Python files, just in case.
sudo rm $MAIL_HOME/*.pyc


# Copy the system/service config files.
echo "Copying system config files..."
sed "s|\(.*\)%MAIL_HOME%\(.*\)|\1$MAIL_HOME\2|g" psiphon-log-rotate.conf > psiphon-log-rotate.tmp 
sudo mv psiphon-log-rotate.tmp /etc/logrotate.d/psiphon-log-rotate.conf
sudo cp 20-psiphon-logging.conf /etc/rsyslog.d/
sudo reload rsyslog
sudo service rsyslog restart


# Create the cron jobs.
echo "Creating cron jobs..."
sudo python create_cron_jobs.py --mailuser $MAIL_USER --normaluser $NORMAL_USER --dir $MAIL_HOME

if [ "$?" -ne "0" ]; then
    echo "Cron creation failed!"
    exit 1
fi

echo "Done"


