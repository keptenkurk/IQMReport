# ****************************************************************************
# * report.py
# * Analyze IQ Messenger report 
#
#
# usage:
# python report.py [options]
# use option -h or --help for instructions
# Options:
# -s sourcefle IQ Messenger report file
# -d destination PDF report file
# -c config configuration JSON file
#
# release info
# 1.0 first release 5-12-20 Paul Merkx
# ****************************************************************************
RELEASE = '1.0 - 05-12-2020'

import time

start = time.time()
print('Report ' + RELEASE + ' by (c) Simac Healthcare.')
print('Disclaimer: ')
print('GEBRUIK VAN DEZE SOFTWARE IS OP EIGEN RISICO')
print(' ')
print('Laden van bibliotheken...')

import sys
import argparse
import os
import pandas as pd
from pandas.core.common import SettingWithCopyWarning
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import seaborn as sns
from datetime import datetime
import json
import warnings


def filewritable(filename):
    try:
        f = open(filename, 'w')
        f.close()
    except IOError:
        print('Kan ' + filename + ' niet schrijven.')
        print('Mogelijk is het bestand geopend in een andere toepassing.')
        return False
    os.remove(filename)
    return True

# Print iterations progress
def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)


# Calculate escalation stage from time between start/finish
def get_runtime(row):
    global df
    global conf
    global count
    global size
    printProgressBar(count, size, prefix = 'Progress:', suffix = 'Complete', length = 50)
    count += 1
    df_tmp = df.loc[(df['Flow UID'] == row['Flow UID'])]
    runtime = df_tmp['Action Date'].max() - df_tmp['Action Date'].min()
    # sometimes runtime exceeds the maximum time a flow could theoretically run
    # so top it off to the "no response" run time
    if runtime.seconds > conf["escalations"][-1]["time"]:
        runtime = datetime.timedelta(seconds = conf["escalations"][-1]["time"]) 
    return runtime.seconds

def get_escalation(row):
    global df
    global conf
    global count
    global size
    printProgressBar(count, size, prefix = 'Progress:', suffix = 'Complete', length = 50)
    count += 1
    escalation = "Unknown"
    for i in conf["escalations"]:
        if row['Runtime'] < i["time"]:
            escalation = i["name"]
            return escalation
    return escalation

# split message in parts and check it for any of the available translations
# in the conf json. Return corresponding Location and AlarmType
def parse_message(rowmessage):
    global conf
    global size
    global count
    printProgressBar(count, size, prefix = 'Progress:', suffix = 'Complete', length = 50)
    splitmsg = rowmessage.split(' ')
    msglen = len(splitmsg)
    alarm_type = "Onbekend"
    alarm_loc = "Onbekend"
    for msg in conf["messages"]:
        # check for keyword and keep indexes witin bounds
        if (((0 <= msg["position"] < msglen) and 
           (splitmsg[msg["position"]] == msg["message"])) or
           ((-msglen <= msg["position"] < 0) and 
           (splitmsg[msg["position"] + msglen] == msg["message"]))):
            alarm_type = msg["Alarm_Type"]
            if msg["Alarm_Loc_from"] == "Action Device Name":
                alarm_loc = "Action Device Name"
            else:
                alarm_loc = ' '.join(splitmsg[msg["Alarm_Loc_from"]:
                                              msg["Alarm_Loc_to"]])
    if alarm_type == 'Onbekend':
        print('Regel met onbekend alarmbericht: ' + rowmessage)
    count += 1
    return alarm_loc, alarm_type


# ***************************************************************
# *** Main program ***
# ***************************************************************

# *** Read arguments passed on commandline
parser = argparse.ArgumentParser()
parser.add_argument("-s", "--sourcefile", nargs=1,
                    help="filenaam/pad voor bron CSV bestand")
parser.add_argument("-d", "--destinationfile", nargs=1,
                    help="filenaam/pad voor PDF bestand")
parser.add_argument("-c", "--commandfile", nargs=1,
                    help="filenaam/pad voor configuratie JSON bestand")
args = parser.parse_args()

if args.sourcefile:
    sourcefilename = args.sourcefile[0]
else:
    sourcefilename = "report.csv"
if not os.path.exists(sourcefilename):
    print("Het CSV report bestand %s is niet gevonden."
          % (sourcefilename))
    sys.exit()

if args.destinationfile:
    destinationfilename = args.destinationfile[0]
else:
    destinationfilename = "report.pdf"
if not filewritable(destinationfilename):
    sys.exit()

if args.commandfile:
    commandfilename = args.commandfile[0]
else:
    commandfilename = "messages.json"
if not os.path.exists(commandfilename):
    print("De configuratie JSON '%s' is niet gevonden."
          % (commandfilename))
    sys.exit()

print('Begin met verwerken IQ Messenger rapport...')

# read messages json
fs = open(commandfilename, 'r')
try:
    if fs.mode == 'r':
        messages_json = fs.read()
    fs.close()
    conf = json.loads(messages_json)
except Exception as e:
    print("Configfile %s is geen geldig JSON bestand:\n %s"
          % (commandfilename, e))
    sys.exit()

# read CSV
try:
    df = pd.read_csv(sourcefilename)
except:
    print("%s is geen geldig IQ Messenger CSV report bestand."
          % (sourcefilename))
    print("Verwerking gestopt")
    sys.exit()

# Get rid of  unneeded columns
df = df.drop(columns=['Action Device Code', 'Action Service Id'])
# Change Action date string to proper timedate format
df['Action Date'] = pd.to_datetime(df['Action Date'],
                                   format="%d.%m.%Y %H:%M:%S.%f")
# create new table with only start of alarms and any of the
# interfaces & flowgroups listed in config JSON
df_alarms = df.loc[(df['Action Type'] == 'Started') &
                   (df['Action Device Item Type'].isin(conf["interfaces"])) &
                   (df['Flow Group'].isin(conf['flowgroups']))]

size = 3 * len(df_alarms.index)
if size == 0:
    print("Geen data in selectie gevonden.")
    sys.exit()
count = 0
printProgressBar(count, size, prefix = 'Progress:', suffix = 'Complete', length = 50)

# Create new Location, AlarmType and Escalation columns based on data
# found in the Message and JSON configuration parameters. Optionally
# ignore "Action Device Name" column as the newly crafted Location
# based on the message is a more generic solution over the projects

warnings.filterwarnings("ignore", category=SettingWithCopyWarning)
df_alarms['Location'], df_alarms['Alarm Type'] = \
    zip(*df_alarms['Message'].map(parse_message))
df_alarms.loc[df_alarms['Location'] == 'Action Device Name', 'Location'] = \
    df_alarms['Action Device Name']

df_alarms['Runtime'] = df_alarms.apply(get_runtime, axis=1)
df_alarms['Escalation'] = df_alarms.apply(get_escalation, axis=1)

date_start = df_alarms['Action Date'].min().strftime('%d/%m/%Y %H:%M')
date_stop = df_alarms['Action Date'].max().strftime('%d/%m/%Y %H:%M')

print()
print('Genereren PDF...')
with PdfPages(destinationfilename) as pdf:
    sns.set(style='darkgrid', rc={'figure.figsize': (8.27, 11.7)})
    sns.set_context("paper")

    # Number of alarms per room stacked by alarmtype
    try:
        df_alarms.groupby(['Location', 'Alarm Type']).size().unstack().\
            plot(kind='barh', stacked=True, width=0.8, fontsize=6)
        plt.title(conf["klantnaam"] + '\nTotaal meldingen per locatie van ' +
                  date_start + ' tot ' + date_stop, loc='left')
        plt.legend(title='Alarmtype', loc='upper right')
        plt.ylabel('Locatie')
        plt.xlabel('Aantal meldingen')
        plt.tight_layout()
        pdf.savefig()
        plt.close
    except:
        print("Fout bij het plotten van Alarmen per Locatie. Grafiek overgeslagen.")

    # Set Action Date as index for the alarms table.
    # This enables graphing daily counts
    df_alarms = df_alarms.set_index('Action Date')

    # Total Number of alarms per day stacked
    try:
        df_alarms.groupby([df_alarms.index.date, 'Alarm Type']).size().unstack().\
            plot(kind='bar', stacked=True)
        plt.title(conf["klantnaam"] + '\nTotaal aantal meldingen per dag van ' +
                  date_start + ' tot ' + date_stop, loc='left')
        plt.legend(title='Alarmtype', loc='upper right')
        plt.xlabel('Datum')
        plt.ylabel('Aantal meldingen')
        plt.tight_layout()
        pdf.savefig()
        plt.close
    except:
        print("Fout bij het plotten van Alarmen per dag. Grafiek overgeslagen.")

    # Total Number of alarms per hour of day stacked
    try:
        df_alarms.groupby([df_alarms.index.hour, 'Alarm Type']).size().unstack().\
            plot(kind='bar', stacked=True)
        plt.title(conf["klantnaam"] + '\nTotaal aantal meldingen per uur van de dag van ' +
                  date_start + ' tot ' + date_stop, loc='left')
        plt.legend(title='Alarmtype', loc='upper right')
        plt.xlabel('Uur')
        plt.ylabel('Aantal meldingen')
        plt.tight_layout()
        pdf.savefig()
        plt.close
    except:
        print("Fout bij het plotten van alarmen per uur. Grafiek overgeslagen.")

    # Escalation state of alarms per day
    try:
        df_alarms.groupby([df_alarms.index.date, 'Escalation']).size().\
            unstack().plot(kind='bar', stacked=True)
        plt.title(conf["klantnaam"] + '\nEscalatie niveau per dag van ' +
                  date_start + ' tot ' + date_stop, loc='left')
        plt.legend(title='Escalatieniveau', loc='upper right')
        plt.xlabel('Datum')
        plt.ylabel('Aantal')
        plt.tight_layout()
        pdf.savefig()
        plt.close
    except:
        print("Fout bij plotten van escalatie niveaus per dag. Grafiek overgeslagen.")

    # Response per employee
    try:
        if conf["includeOfflineUser"] == "Ja":
            df_resp = df.loc[(df['Action Type'] == 'Received response')] 
        else:
            df_resp = df.loc[(df['Action Type'] == 'Received response') & 
                (df['Action Response'] != 'User is offline')]             
        df_resp.groupby(['Action Device Name', 'Action Response']).size().\
            unstack().plot(kind='barh', stacked=True)
        plt.title(conf["klantnaam"] + '\nOntvangen reponses van ' + date_start +
                  ' tot ' + date_stop, loc='left')
        plt.legend(title='Responsetype', loc='upper right')
        plt.ylabel('Medewerker')
        plt.xlabel('Response')
        plt.tight_layout()
        pdf.savefig()
        plt.close
    except:
        print("Fout bij het plotten van responses per medewerker. Grafiek overgeslagen.")
        
    # Average responsetime and number of alarms downsampled per hour 
    try:
        df_run = df_alarms.resample("1h").agg({'Runtime':'mean','Action Type':'count'})
        df_run.plot(subplots=True, layout=(2,1), style=['r', 'b'], grid=True, title=['Gem.Responsetijd over 1u','Aantal meldingen in 1u'])   
        plt.xlabel('Tijd')
        plt.tight_layout()
        pdf.savefig()
        plt.close
    except:
        print("Fout bij het plotten van responsetijd per uur. Grafiek overgeslagen.")

end = time.time()
exectime = round(1000*(end-start))
print("Rapportage verwerkt in ", exectime/1000.0, "seconden.")
