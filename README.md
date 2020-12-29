# IQMReport
Het CSV rapport in IQ Messenger is prima voor het analyseren van gebeurtenissen op een bepaald moment maar geeft geen overzicht over wat er zich over langere tijd afspeelt. Hiervoor is de IQ Messenger report tool gemaakt. De aantallen meldingen in de CSV worden geteld en in staafdiagrammen weergegeven. 
# Gebruik 
Omdat de vorm van de rapportage afhankelijk is van de inrichting van e flows in het project is er een manier nodig om het programma te vertellen naar welke regels te zoeken. Dit gaat via een configuratiefile “messages.json” die per project verschillend is. 
Open een DOS venster en typ
`report <enter>` 
of start het script in Python3 met
`python report.py`
Het programma opent default het bestand “report.csv” en maakt “report.pdf” aan de hand van “messages.json”. Alle bestanden worden verwacht in de huidige directory. Is dit niet het geval, of hebben de bestanden een andere naam, gebruik dan (een of meer van) de parameters -s, -d en -c als volgt: `report -s bronbestand.csv -d doelbestand.pdf -c configbestand.json`
Tip: het report.pdf wordt overschreven maar dat lukt niet wanneer dit bestand geopend is. 
Na enige tijd (ca 30 sec) is het pdf bestand gemaakt met daarin de volgende overzichten: 
* Totaal aantal meldingen per kamer gestapeld naar type alarm 
* Totaal aantal meldingen per dag gestapeld naar type alarm 
* Totaal aantal meldingen per uur van de dag gestapeld naar type alarm 
* Totaal aantal meldingen per dag gestapeld naar escalatie niveau 
* Ontvangen responses per gebruiker gestapeld per type response 

# Werking 
Voor het weergeven van de grafieken wordt de data uit de CSV file bewerkt op basis van de gegevens in “messages.json”. Deze JSON heeft 4 onderdelen: 
* klantnaam: De naam van de klant zodat die in de PDF kan worden weergegeven  
* messages: De auto-generated messages waarin gezocht moet worden. Met iedere onderdeel de velden: 
  * "message": "sensoren",    // de naam van het alarm zoals deze in de message staat 
  * “position":  1,   // de positie in de message (0=eerste woord, 1=tweede woord etc, -1=laatste woord, -2 is voorlaatste woord etc) 
  * "Alarm_Type": "Techn.Probleem met sensoren", // Hoe alarm in PDF genoemd wordt 
  * “Alarm_Loc_from": 4,      // De alarm locatie staat van from tot to in de message 
  * "Alarm_Loc_to": 7         // als “Alarm_Loc_from”: “Action Device Name” dan wordt  
                              // de from en to genegeerd en wordt de locatie uit de CSV kolom 
                              // “Action Device Name” toegepast. 
* interfaces: De lijst met interfaces (Action Device Item Type in de CSV) waarop gefilterd moet worden. 
* flowgroups: De lijst met flowgroups (Flow Group in de CSV) waarop gefilterd moet worden. 
* escalations: De escalatieniveaus die in de flows gemaakt zijn. Iedere escalatie heeft een 
  * “name”: “1e”   // De naam waaronder dit escalatieniveau in de PDF genoemd wordt  
  * “time”: 180    // Tijd in seconden tussen begin en einde van de flow voor dit escalatieniveau.
                   // Tip: Tel de tijden van de escalatieniveaus op voor de juiste werking. 

# Voorbeeld 
Voorbeeld van het decoderen van een message string tot locatie en alarmtype: 
De melding:  
drukknop_actief RH DK3 KMR K3.82 bevindt zich in RH DK3 Huiskamer2 Raamhof 
wordt array 
[‘drukknop_actief’, ‘RH’, ‘DK3‘, ‘KMR‘, ‘K382‘, ‘bevindt‘, ‘zich‘, ‘in‘, ‘RH‘, ‘DK3‘, ‘Huiskamer2‘, ‘Raamhof‘]
   0                  1     2      3      4         5        6      7      8     9        10            11 

Door in de JSON aan te geven: 
{'message': 'drukknop_actief', 
   'position': 0, 
   'Alarm_Type': 'Drukknop', 
   'Alarm_Device_from': 1, 
   'Alarm_Device_to': 5}, 

Betekent dit dat: 
Het soort alarm is drukknop_actief en heeft de positie index 0 in het array van de melding (array start bij 0). Het alarmtype willen we in de PDF “Drukknop” noemen. De unieke locatie wordt in de PDF “RH DK3 KMR K382” genoemd (posities 1 tot 5 in het array, dus 1 t/m 4).  
Als het handiger is om voor de locatie het veld “Action Device Name” te gebruiken (bijv. wanneer deze een gebruikersnaam heeft met soms 2 en soms 3 delen) vul je bij “Alarm_Device_from”: “Action Device Name” in. De Alarm_Device_to waarde wordt dan genegeerd. 

# Voorbeeld JSON: 

    { 
      "klantnaam" : "Careforyou", 
      "messages": [ 
      { 
          "message": "Alarmknop", 
          "position": 0, 
          "Alarm_Type": "*Alarmknop", 
          "Alarm_Loc_from": "Action Device Name", 
          "Alarm_Loc_to": 3 
      }, 
      { 
          "message": "Inactiviteit", 
          "position": 0, 
          "Alarm_Type": "*Inactiviteit",     
          "Alarm_Loc_from": "Action Device Name", 
          "Alarm_Loc_to": 4 
      }, 
      { 
          "message": "bedsensor", 
          "position": 1, 
          "Alarm_Type": "Techn.Sensor uitgetrokken", 
          "Alarm_Loc_from": "Action Device Name", 
          "Alarm_Loc_to": 4 
       } 
       ],
      "interfaces" : [
          "sensara"
       ],
      "escalations": [ 
        {
          "name": "1.Primair", 
          "time": 180 
        }, 
        {
           "name": "2.Secundair", 
           "time": 360 
        } 
      ], 
      "flowgroups": [ 
          "Locations" 
      ]
    }
