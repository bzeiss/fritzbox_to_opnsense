# fritzbox_to_opnsense
Tools, die bei dem Umstieg von einer AVM Fritzbox nach OPNSense unterstüzen.

*Work in Progress*

Die Software setzt auf die FritzBox Tools (https://www.mengelke.de/Projekte/FritzBox-Tools) von Michael Engelke auf.
Liest man mit diesen Tools die Fritzbox Konfiguration aus, so befindet sich in dem Verzeichnis mit den Konfigdateien eine ar7.cfg, die z.B. DHCP Informationen der FritzBox bereithält.

```
fb_tools.php passwort@ip Konfig eXTrakt-DeCrypt config-dateien
```

Die ar7.cfg liegt in einem zumindest mir nicht bekannten Configdatei-Format vor. Damit dies einfach weiterzuverarbeiten ist, existiert in diesem Repository ein ANTLR4 basierter Python parser (https://github.com/antlr/antlr4), welcher die ar7.cfg in ein JSON Format umwandelt. Die run.sh ist ein Beispiel wie der Lexer und Parser Code generiert werden muss, damit in Folge das Python Skript aufgerufen werden kann, welches die ar7.cfg in ein einfach zu verarbeitendes JSON Format umwandelt.

Plan ist, dass die Inhalte wie z.B. feste DHCP Adressen, Adressbereiche, DNS Namen etc. ausgelesen werden, um sie z.B. über die API wieder in OPNSense hinein zu laden, um ein möglichst einfache und schmerzlose Migration zu nach OPNSense ermöglichen.
