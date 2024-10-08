# fritzbox_to_opnsense

Tools, die bei dem Umstieg von einer AVM Fritzbox nach OPNSense unterstüzen.

Die Software setzt auf die FritzBox Tools (https://www.mengelke.de/Projekte/FritzBox-Tools) von Michael Engelke auf. Mit Hilfe dieser Tools lässt sich eine ar7.cfg und vpn.cfg Datei von der FritzBox auslesen, in der viele Informationen drin stehen, die für eine Migration nach OPNsense erforderlich sind.

Die Config-Dateien liegt in einem eigenen Format vor. Damit dies einfach weiterzuverarbeiten ist, existiert für dieses Format ein ANTLR4 Lexer und Parser. Aufbauend auf diesen, existieren in diesem Repository diverse Skripte, die bei einer Migration unterstützen können.

Dies sind keine Skripte, die von Anfängern verwendet werden sollten. Sie stellen keine schlüsselfertige Lösung für eine Migration dar, sondern sind das Resultat dessen, was ich persönlich für meine Migration benutzt habe und sind eher als Ansatzpunkt bzw. Migrationstoolbox zu verstehen. Netzwerkkonfigurationen und die genutzten Netzwerkfunktionalitäten unterscheiden sich je nach Netzwerk. Es kann sein, dass nicht alle Inhalte migriert werden. Die Skripte sind bewusst in Ihrer Struktur technisch einfach gehalten, so dass diese bei Bedarf für die eigene Migration einfach angepasst werden können ohne sich viel in eine Projektstruktur einzuarbeiten.

Ich übernehme keine Verantwortung und Haftung für Schäden, die durch die unsachgemäße Nutzung dieser Skripte verursacht werden. Ich bearbeite keine Feature Requests oder Änderungswünsche. **Dies ist und wird kein schlüsselfertiges Migrationstool!**

## Bekannte TODOs
- [x] Config Parser für IPv6 überarbeiten. Es werden noch nicht alle validen Formate akzeptiert.
- [ ] Port Forwardings migrieren
- [ ] DynDNS migrieren?

## Dependencies

- Python 3
- ANTLR 4
- ANTLR 4 Python 3 Binding
- PHP 8 (für FritzBox Tools)

Wie diese installiert werden unterscheidet sich je nach Betriebssystem. Z.B. bei Fedora Linux wären dies folgende Schritte:
```
dnf install antlr4 antlr4-runtime python3-antlr4-runtime python3 php-cli
```

## ar7.cfg und vpn.cfg mit FritzBox-Tools extrahieren

Die Software setzt auf die FritzBox Tools (https://www.mengelke.de/Projekte/FritzBox-Tools) von Michael Engelke auf. Mit diesen kann man die Konfigurationsdateien extrahieren und decrypten. Dies ist mit dem folgenden Kommando möglich:

```
fb_tools.php passwort@ip Konfig eXTrakt-DeCrypt config-dateien
```

In dem Zielpfad sollte nun eine entschlüsselte ar7.cfg liegen, die für die weiteren Tools als Input benutzt werden kann. Hier stehen Informationen drin wie etwa:
- Interfaces
- DHCP Reservierungen
- Provider Zugangsdaten
- VPN Konfigurationen
- etc.

Ebenso liegt dort eine vpn.cfg. Dort sind VPN Konfigurationen der FritzBox enthalten.

## ANTLR 4 Lexer und Parser generieren

Im Verzeichnis liegt ein Bash-Skript gen.sh. Dies zeigt wie Lexer und Parser generiert werden müssen. Dieser Code muss generiert werden bevor die anderen Skripte ausgeführt werden.

## ar7.cfg in JSON Objekt umwandeln
Hier für kommt das tool ar7_to_json zum Einsatz. Also Kommandozeilenparameter wird die von den FritzBox-Tools extrahierte ar7.cfg übergeben. Es wird als Ergebnis ein umgewandeltes JSON Objekt auf stdout geschrieben. Dieses kann dann in eine Datei umgeleitet werden.

```
/bin/python3 ar7_to_json.py ../tests/fb/ar7.cfg 2>&1 >ar7.json
```

Ab hier kann das ar7.cfg json Objekt in eigenen Tools weiterverarbeitet werden.

## OPNsense API Key und Secret erzeugen
Damit die Skripte funktionieren, benötigt man einen Nutzer mit API-Key und Secret in OPNsense. Den API-Key und Secret generiert man sich über User in OPNsense über System->Access->Users. 

Der "unsaubere" schnelle Weg wäre einfach dem root user ein API key mit allen Rechten zugeben und diesen dann nach der Skriptausführung wieder zu löschen. Der "saubere" Weg wäre einen neuen Nutzer anzulegen, welcher nur die erforderlichen Rechte hat mit seinem API Key. Dieser kann dann wieder entfernt werden oder bleiben je nach Sicherheitsbedarf. 

In jedem Fall muss man den zugehörigen Nutzer editieren, runterscrollen und im Bereich "API Keys" das "+" drücken und danach auf Save drücken. Es wird dann automatisch eine Datei heruntergeladen, wo API-Key und Secret drin stehen. Diese werden benötigt, um die config.json für die Migrationsskripte zu konfigurieren.

## config.json für OPNsense REST API Verbindungsaufbau

Die Ausführung aller Skripte, die die REST API von OPNsense verwenden, erfordern eine config.json im Verzeichnis oder eine config.json mit einem alternativen Namen, wo die Verbindungsparameter zu OPNsense hinterlegt werden. Alternative config.json-Dateien müssen mit dem Kommandozeilenparameter --config dem Skript mitgeteilt werden kann. In der config.json.template liegt eine Vorlage dieser config.json Datei vor. Am besten man kopiert sich diese nach config.json und passt diese an. Die Inhalte dieser config.json sollten selbsterklärend sein.

## FritzBox DHCP Konfiguration migrieren

Das Skript "ar7_dhcp4_to_opnsense_kea.py" migriert folgende Bestandteile aus der ar7.cfg zu OPNsense in genau dieser Reihenfolge:
1. Interfaces
1. DHCP Reservierungen

Die Migration erfolgt zu dem KEA DHCP Server. Dieser ist relativ neu in OPNsense enthalten. Eine Migration zu ISC DHCP macht jedoch keinen Sinn mehr, da dieser von ISC bald nicht mehr weitergepflegt werden wird und somit auch irgendwann aus OPNSense entfernt werden wird.

Wichtig vor der Ausführung ist, dass ein leerer Zustand der KEA DHCP Server Konfiguration vorausgesetzt wird. Dieser wird nicht vom Skript selbst geleert. Es wird nicht geprüft, ob sich Interfaces oder Reservierungen überlagern oder ähnlich. Das Skript nimmt wirklich nur dumm die vorhandenen Interfaces aus der ar7.cfg und lädt diese über die REST API von OPNsense in die KEA DHCP Server Konfiguration rein. Es findet keine Fehlerbehandlung statt.

Liegt nun eine korrekte config.json vor, so lässt sich das Skript ausführen mit:

```
/bin/python3 ar7_dhcp4_to_opnsense_kea.py ../tests/fb/ar7.cfg 2>&1
```

Bei Erfolg, sollten im Anschluss in OPNsense unter Services->Kea DHCP->Kea DHCPv4 Subnetzs und Reservations existieren.

Sind in den reservations hostname oder hostnamen in den Descriptions leer, so ist in der FritzBox der neighbour name nicht gesetzt. Die Liste ist daher vermutlich sinnvollerweise nachträglich zu prüfen in Hinblick auf z.B. folgende Punkte:

- Hostname leer?
- Prüfung auf Doppeleinträge. Die FritzBox Liste von statischen Mappings räumt sich nicht selbst auf und wächst mit der Zeit etwas wild. Bei mir waren einige IP Adressen sogar für unterschiedliche MAC Adressen doppelt vergeben.
- Soll der host ggf. doch nicht migriert werden?
- Aktivierung der KEA DHCP Interfaces
- KEA DHCP gestartet? Wenn er nicht hochfährt, Logfiles vom DHCP lesen und Problem finden
- Wenn Unbound DHCP benutzt wird und die DHCP Einträge als DNS Namen verwendet werden sollen: Services->Unbound DNS->Register DHCP Static Mappings => true

## OPNsense DHCP Konfiguration zurücksetzen

Das Skript clean_opnsense_kea_dhcpv4.py kann DHCPv4 Subnetze und Reservierungen in der OPNsense KEA Konfiguration komplett entfernen, falls ein zweiter Durchlauf stattfinden soll. Wichtig: es finden keine Rückfragen zu Sicherheit oder ähnliches statt. Wird das Skript ausgeführt, so werden Interfaces und Reservierungen komplett und ausnahmslos gelöscht, auch solche, die nicht vom Migrationsskript stammen, sondern ggf. von Hand angelegt worden sind!

```
/bin/python3 clean_opnsense_kea_dhcpv4.py
```

## OPNsense WAN Interface für Telekom PPPoE konfigurieren
Leider deckt die OPNsense API das die Interface Konfiguration noch nicht vollständig ab bzw. setzt eine andere Vorgehensweise als die Nutzung der API voraus, weshalb wir hier teilweise per Skript und teilweise von Hand arbeiten müssen.

Vorausgesetzt wird, dass ein WAN port bereits existiert. Dieser wird normalerweise mit der Installation von OPNsense eingerichtet. Der Name von diesem muss als zweiter Kommandozeilenparameter mit übergeben werden.

In den Skript passieren zwei Dinge:
- Es wird ein VLAN 7 Interface erstellt und an das WAN interface gehangen
- Der PPPOE Username und das PPPOE Passwort werden ausgegeben.

```
/bin/python3 ar7_telekom_to_opnsense_pppoe.py ../tests/fb/ar7.cfg WAN
```

Mit dem PPPoE Username und PPPoE Passwort muss nun über das OPNsense Web Inteface manuell eine Umkonfiguration vorgenommen werden.

In Interaces->WAN werden folgende Anpassungen vorgenommen:

1) Unter der Überschrift "Basic configuration"
   - Enable Interface: true
   - Prevent interface removal: true
1) Unter der Überschrift "Generic configuration":
   - IPv4 Configuration Type: PPPoE
   - MTU: 1492 (für DSL/VDSL, sonst wahrscheinlich 1500)
2) Unter der Überschrift "PPPoE configuration"
   - Username: [auf den PPPoE Username aus dem Skript setzen]
   - Password: [auf das PPPoE Passwort aus dem Skript setzen]
3) In DHCPv6 client configuration:
   - User IPv4 connectivity: true
   - Prefix Delegation size: 56
   - Request prefix only: true
4) Save
5) Apply Changes

Nach dem "Apply Changes" sollte sich das WAN interface in das device "pppoeX" umgewandelt haben.

## FritzBox Wireguard Konfigurationen/Profile migrieren

Die Wireguard VPN Konfigurationen befinden sich nicht in der ar7.cfg, sondern in der vpn.cfg.

Der Aufruf erfolgt mit

```
/bin/python3 vpn_wireguard_to_opnsense.py --clean --addrules ../tests/fb/vpn.cfg
```
Die beiden Parameter --clean und -addrules sind optional. --clean löscht alle wireguard instance und peers bevor die neuen eingerichtet werden. --addrules erzeugt zwei Regeln für das WAN interface, um den Zugriff auf den Wireguard Port (bei der FritBox standardmäßig nicht auf 51820) auf der OPNSense Firewall zuzulassen. Auf der wireguard group werden eingehende Pakete auf alle Netze zugelassen (ebenso IPv4 und IPv6). Insbesondere die letztere Regel ist ggf. nicht immer so gewünscht und zu offen. Es sollte daher sorgfältig geprüft werden, um diese Regel weiter eingeschränkt werden muss. Die Firewall Regeln sind nach der automatischen Anlage im Bereich Firewall->Automation zu finden und können auch nur dort weiter editiert oder entfernt werden. Ggf. muss in der Automation Konfiguration noch auf Apply geklickt werden, die apply rules scheinen nicht immer zuverlässig zu gehen.

Ich empfehle unbedingt nur die Tutorials von der offiziellen OPNsense Anleitung als Referenz zu benutzen (Site-to-Site: https://docs.opnsense.org/manual/how-tos/wireguard-s2s.html, Road Warrior Setup: https://docs.opnsense.org/manual/how-tos/wireguard-client.html). Ich habe selbst sehr viel Zeit darauf verwenden müssen Probleme mit meiner VDSL Verbindung zu analysieren, die v.a. dadurch entstanden sind, dass andere Anleitungen einzelne Schritte übersprungen sind. Herauszuheben hierbei:
1. Man sollte das Wireguard Interface hinzufügen. Man kann zwar auch mit der Wireguard Group arbeiten (diese arbeitet über alle Wireguard Instanzen), die Konfiguration pro Interface ist aber vorteilhaft und feingranularer. Insbesondere lässt sich danach auf dem Wireguard Interface MTU setzen. Bei einer VDSL Verbindung sollte der MTU Wert für das Wireguard Interface meinen Informationen nach auf 1412 stehen. Insbesondere, wenn man auch das Internet über das VPN tunneln möchte, wird über das Interface automatisch eine NAT Outbound Regel angelegt, die sonst fehlen würde und manuell eingerichtet werden müsste.
2. In der Wireguard Instanz wird durch die Skripte auch automatsch ein MTU Wert 1412 gesetzt (sichtbar, wenn man im Web Interface den Advanced Mode einstellt).
3. In vielen Installationsanleitungen wird der Schritt des MSS Clampings übersprungen. In meinem Setup war es so, dass ich bei einer stehenden Wireguard Verbindung zwar pingen konnte, aber nicht auf Webseiten in meinem Netz zugreifen konnte. Dieses Problem verschwand, nachdem ich in Firewall->Settings->Normalization ein Setting für das Interface "WireGuard (Group)" eingerichtet habe, wo ich unter "Normalizations" Max mss auf 1352 gesetzt habe (für IPv4 und IPv6).
4. Zu beachten: die MTU Settings und MSS Clampings sind ggf. anders setzen, wenn man nicht mit DSL/VDSL, sondern mit Kabel, Glasfaser, etc. arbeitet.

Weiterhin ist anzumerken, dass die Migration nicht ganz ohne manuelle Eingriffe bei den Road Warrior Setups möglich ist. Die Tunnel Interface Konfiguration der FritzBox ist nicht ganz nachvollziehbar und scheint sich nicht ganz am Standard zu orientieren. Die Skripte funktionieren so, dass ein Tunnel Interface 10.10.10.1/24 für die Wireguard-Instanz eingerichtet wird und die Road Warrior Setups danach aufsteigend Adressen 10.10.10.2, 10.10.10.3 etc. erhalten. Durch diese neu vergebenen Adressen müssen die Adressen in bereits konfigurierten Wireguard Clients angepasst werden. Diese stehen mit einer /32-er Adresse im eigentlichen Netzwerk, nicht im Tunnel-Netzwerk in den Client Konfigurationen. Diese müssen so gesetzt werden wie in der Peers-Übersicht unter Allowed IPs die Road Warrior Peers stehen (enden auf /32). Ich habe probiert das ganze so zu bauen wie es in der Fritzbox war, dann hat das Routing allerdings wiederum nicht korrekt funktioniert. Ich denke der nun verfolgte Ansatz ist eine Kompromiss, der für mich zumindest funktioniert hat. Die site-to-site Verbindungen scheinen ohne weitere Anpassungen zu funktionieren.

Ebenso zu beachten ist, dass ggf. Dynamic DNS notwendig ist, damit Peers auf die OPNSense drauf kommen. Diese Konfiguration ist durch die Skripte derzeit nicht abgedeckt.

