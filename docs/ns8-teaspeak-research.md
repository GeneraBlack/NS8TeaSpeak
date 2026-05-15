# NS8 TeaSpeak Research

## Ziel

Eine NethServer-8-Applikation fuer einen TeaSpeak-Server bauen, die auf belastbaren Upstream-Quellen basiert und spaeter ohne grobe Architekturwechsel in ein echtes NS8-Modul umgesetzt werden kann.

## Kurzfazit

- Technisch ist ein NS8-Modul fuer TeaSpeak machbar.
- Die richtige Basis ist ein rootless NS8-Modul auf Grundlage von NethServer/ns8-kickstart.
- Der kritische Punkt ist nicht NS8, sondern Upstream: das offizielle Docker-Repository TeaSpeak/TeaDocker existiert, aber das erwartete Docker-Hub-Image teaspeak/server ist aktuell nicht abrufbar.
- Fuer ein stabiles NS8-Modul sollte der Server daher nicht blind von Docker Hub gezogen werden, sondern aus dem offiziellen TeaDocker-Dockerfile oder direkt aus dem offiziellen TeaSpeak-Tarball reproduzierbar selbst gebaut werden.
- Upstream wirkt weitgehend eingefroren: TeaSpeak-Server-Repo zuletzt 2021 aktualisiert, TeaDocker 2022, das aktuelle amd64_stable-Release im offiziellen Repo ist 1.5.6.

## Empfohlene Modulstrategie

### Empfehlung fuer MVP

- Rootless NS8-Modul.
- Ein Hauptdienst teaSpeak.service, der den TeaSpeak-Server in Podman startet.
- Vorerst kein separater TeaWeb-Container im MVP.
- Feste Standardports gemaess TeaSpeak-Upstream.
- Maximal eine Instanz pro Node, solange keine Portkonfiguration pro Instanz implementiert ist.
- Eigener Build fuer das Service-Image statt Abhaengigkeit von einem aktuell nicht bestaetigten Docker-Hub-Server-Image.

### Empfehlung fuer Phase 2

- Optionaler zweiter Dienst fuer TeaWeb.
- Konfigurierbare Ports pro Instanz.
- Optional externe MySQL-Datenbank.
- Optional Anzeige oder Download der Bootstrap-Credentials ueber die UI.

## Relevante TeaSpeak-Upstream-Fakten

### Upstream-Zustand

- Offizielles Docker-Repo: TeaSpeak/TeaDocker.
- TeaDocker enthaelt Dockerfiles fuer Server und Web-Client.
- Das GitHub-Repo TeaDocker wurde zuletzt im Mai 2022 aktualisiert.
- Das GitHub-Repo TeaSpeak wurde zuletzt im Mai 2021 aktualisiert.
- Das offizielle TeaSpeak-Binary-Repository fuer Linux zeigt nur amd64_stable.
- Der aktuelle Wert in repo.teaspeak.de/server/linux/amd64_stable/latest ist 1.5.6.
- Der Index des offiziellen Repos zeigt TeaSpeak-1.5.6.tar.gz als neuestes Serverarchiv.

### Architektur und Plattform

- Praktisch nur amd64 bzw. x64 ist belastbar belegt.
- Fuer ARM gibt es in den offiziellen Serverquellen keinen belastbaren Hinweis auf Support.
- Das Modul sollte deshalb explizit als x86_64 bzw. amd64-only betrachtet werden.

### Docker-Lage

- TeaDocker dokumentiert den Server unter dem Namen teaspeak/server.
- Die direkte Docker-Hub-URL fuer teaspeak/server lieferte in der Recherche HTTP 404.
- Daraus folgt: Das NS8-Modul sollte den Server nicht als unveraenderliche externe Image-Abhaengigkeit voraussetzen.
- Sicherer ist ein eigenes Image-Build mit gepinnter Version 1.5.6.

### Server-Ports

Aus den offiziellen TeaDocker-Dockerfiles und der Default-Konfiguration ergeben sich diese relevanten Ports:

- 9987/udp: Standard-Voice-Port.
- 9987/tcp: wird vom offiziellen Container ebenfalls exposed.
- 10101/tcp: Query-Port.
- 30303/tcp: File-Port.

Die Default-Konfiguration des Servers belegt zusaetzlich:

- binding.query.port = 10101
- binding.file.port = 30303
- voice.default_port = 9987

### Persistente Daten im offiziellen Container

Das offizielle TeaDocker-Setup verwendet diese Persistenzpfade:

- /ts/logs
- /ts/certs
- /ts/config
- /ts/files
- /ts/database
- /ts/crash_dumps

Diese Pfade sollten im NS8-Modul jeweils auf benannte Podman-Volumes gemappt werden.

### Startkommando und Datenbank

Das offizielle TeaDocker-Image startet den Server mit:

- Entry point: ./TeaSpeakServer
- Default-CMD: -Pgeneral.database.url=sqlite://database/TeaData.sqlite

Wichtige Folge:

- SQLite ist fuer den MVP ausreichend und der einfachste Standard.
- Eine externe MySQL-Anbindung ist spaeter moeglich, aber nicht fuer den ersten Wurf noetig.

### Wichtige Konfigurationsoptionen aus default_files/config.yml

Relevante Defaults aus der Upstream-Standardkonfiguration:

- general.database_url = sqlite://TeaData.sqlite
- general.license = none
- general.crash_path = crash_dumps/
- binding.query.host = 0.0.0.0
- binding.query.port = 10101
- binding.file.host = 0.0.0.0
- binding.file.port = 30303
- voice.default_port = 9987
- query.enableSSL = 2
- query.ssl.certificate = certs/query_certificate.pem
- query.ssl.privatekey = certs/query_privatekey.pem
- web.enabled = 1
- web.ssl.certificate = certs/default_certificate.pem
- web.ssl.privatekey = certs/default_privatekey.pem
- music.enabled = 1
- vpn.enabled = 0

### Bootstrap-Credentials

Das offizielle TeaDocker-README weist darauf hin:

- Beim ersten Start werden ServerQuery-Passwort und Server-Admin-Privilege-Key in den Logs ausgegeben.
- Diese Werte werden fuer die Administration benoetigt.
- Der Upstream empfiehlt ausdruecklich, sie sofort zu notieren.

Wichtige Konsequenz fuer NS8:

- Das Modul braucht eine definierte Strategie, um diese Initial-Credentials abzufangen.
- Diese Werte sollten nicht einfach roh in die normale Environment-Datei geschrieben werden.
- Besser ist eine dedizierte State-Datei oder ein eigenes Secret-/State-Handling mit UI-Anzeige nur bei Bedarf.

## Relevante NS8-Fakten fuer die Umsetzung

### Modulbasis

- Neues Modul auf Basis von NethServer/ns8-kickstart.
- Repository-Name mit Praefix ns8-.
- Wichtige Bestandteile des Moduls:
  - imageroot
  - ui
  - build-images.sh
  - README.md

### Rootless-Modell

- Rootless ist fuer diesen Anwendungsfall die richtige Wahl.
- TeaSpeak benoetigt keine privilegierten Ports kleiner 1024.
- Rootless-Module laufen unter einem eigenen Unix-Benutzer.
- Systemd-Units liegen bei rootless unter ~/.config/systemd/user.
- Podman-Volume-Namen sind bei rootless privat und kollidieren nicht global.

### Actions und Modul-Lifecycle

Das Modul braucht mindestens diese Actions:

- create-module: initiale Vorbereitung, optional Firewall-Oeffnungen fuer Standardports.
- configure-module: Eingaben validieren, Umgebung schreiben, Konfiguration expandieren, Dienste starten.
- get-configuration: aktuelle Konfiguration fuer die UI lesen.
- get-status: Dienststatus, Version, Volumes und Ports fuer die UI bereitstellen.
- destroy-module: Dienste stoppen, Firewall-Regeln entfernen, Traefik-Routen nur falls wirklich genutzt.

### Systemd-User-Unit

NS8 erwartet mindestens eine Systemd-Unit, die:

- beim Boot aktiviert wird,
- Podman-Prozesse startet und stoppt,
- bei Fehlern neugestartet wird.

Wichtige Muster aus der NS8-Dokumentation:

- EnvironmentFile=%S/state/environment kann fuer kontrollierte Werte genutzt werden.
- Fuer frei eingegebene oder zufaellige Geheimnisse ist diese Datei ungeeignet.
- ExecStartPre kann ueber runagent Hilfskommandos ausfuehren.

### Image-Labels, die fuer TeaSpeak relevant sind

Im build-images.sh werden fuer das Modul voraussichtlich diese Labels benoetigt:

- org.nethserver.rootfull=0
- org.nethserver.authorizations=node:fwadm
- org.nethserver.images=<eigenes TeaSpeak-Service-Image>
- org.nethserver.volumes=<Liste der benutzten Named Volumes>
- org.nethserver.max-per-node=1

Hinweise dazu:

- org.nethserver.max-per-node=1 ist fuer den MVP sinnvoll, solange wir mit festen Ports arbeiten.
- Falls spaeter frei konfigurierbare Ports kommen, kann diese Begrenzung neu bewertet werden.

### Port- und Firewall-Strategie

NS8 kennt zwei verschiedene Themen:

- zufaellige Portallokation ueber org.nethserver.tcp-ports-demand und org.nethserver.udp-ports-demand,
- direkte Oeffnung fester Ports ueber die Node-Firewall mit node:fwadm.

Fuer TeaSpeak ist die bessere MVP-Strategie:

- feste Standardports 9987/udp, 9987/tcp, 10101/tcp und 30303/tcp,
- Oeffnung dieser Ports per agent.add_public_service(),
- keine zufaellige NS8-Portallokation fuer die Erstversion.

Begruendung:

- Ein Voice-Server wird typischerweise ueber bekannte Ports dokumentiert.
- Zufallsports sind fuer Clients und Support unpraktisch.
- Fixed Ports passen besser zu TeaSpeak-Upstream und zu der Erwartung der Benutzer.

Offene Folge:

- Der MVP sollte pro Node nur eine Instanz zulassen.

### Netzwerkmodus

Moegliche Wege in NS8:

- podman run mit --publish
- oder --network=host

Empfehlung fuer TeaSpeak im MVP:

- Kein Host-Networking erzwingen.
- Normales Port-Publishing mit klaren Publish-Regeln verwenden.
- Firewall-Regeln explizit vom Modul verwalten.

Das ist einfacher nachvollziehbar und besser mit dem NS8-Modell vereinbar.

### Volumes in NS8

Die Upstream-Pfade sollten auf Named Volumes abgebildet werden, zum Beispiel:

- logs -> /ts/logs
- certs -> /ts/certs
- config -> /ts/config
- files -> /ts/files
- database -> /ts/database
- crash-dumps -> /ts/crash_dumps

Sinnvolle Kandidaten fuer org.nethserver.volumes:

- files
- database
- logs
- crash-dumps

Diese Daten profitieren am ehesten von optionalen Zusatzdatentraegern.

### UI-Anforderungen in NS8

NS8-Module sollten mindestens diese Seiten haben:

- Status
- Settings
- About

Fuer TeaSpeak bedeutet das konkret:

#### Status

- Systemd-Service-Status.
- Installations-Node.
- Gemappte Ports.
- Verwendete Volumes.
- Server-Version.
- Optional Hinweis, ob Bootstrap-Credentials bereits gesichert wurden.

#### Settings

Sinnvolle MVP-Felder:

- Instanz-Label.
- Zeitzone.
- Optional Query-SSL aktivieren oder beibehalten.
- Optional Web-Zugang aktivieren oder deaktivieren.
- Optional Music-Feature aktivieren oder deaktivieren.

Nicht fuer MVP noetig:

- Vollstaendige Bearbeitung der kompletten config.yml.
- Externe MySQL-Konfiguration.
- Feingranulare Thread-Tuning-Parameter.

#### About

- Modulmetadaten.
- Quellcode-URL.
- Dokumentation.
- Bug-Tracker.
- Upstream-Hinweise.

### Testing in NS8

ns8-kickstart bringt bereits die Standard-Teststruktur mit. Fuer TeaSpeak sollten mindestens diese Faelle in Robot-Tests abgedeckt werden:

- Modul laesst sich via add-module installieren.
- UI-Seiten Status, Settings und About laden.
- configure-module startet den Dienst erfolgreich.
- Die erwarteten Ports sind offen.
- Logs enthalten beim ersten Start die Bootstrap-Informationen oder ein Modul-Action kann diese lesen.
- remove-module entfernt Dienst und Firewall-Regeln sauber.

## Empfohlener technischer Zuschnitt des Moduls

### Service-Image

Empfehlung:

- Eigenes Image im Modulprojekt bauen.
- TeaDocker/server als Vorlage nutzen.
- SERVER_VERSION fest auf 1.5.6 pinnen.
- Debian-Variante als konservative Basis bevorzugen.

Begruendung:

- Docker-Hub-Verfuegbarkeit von teaspeak/server ist aktuell nicht belastbar.
- Pinning verhindert unkontrollierte Upstream-Aenderungen.
- Debian ist fuer spaetere Diagnose meist angenehmer als Alpine-glibc.

### Podman-Run-Skizze fuer die spaetere Systemd-Unit

Benutzt werden muessen:

- ein eigenes Service-Image,
- sechs benannte Volumes,
- feste Port-Mappings,
- Restart bei Fehlern,
- ein eingeblendetes config.yml oder ein generierter Konfigurationsstand in /ts/config.

### Konfigurationsdatei

Empfehlung fuer den MVP:

- Eine schmale template-basierte config.yml generieren.
- Nur wenige, wirklich benoetigte Schalter parametrisieren.
- Alles andere beim Upstream-Default lassen.

Das vermeidet eine UI, die sofort zu gross wird.

## Wichtigste Risiken

### 1. Upstream-Stagnation

- TeaSpeak und TeaDocker wirken nicht aktiv gepflegt.
- Ein NS8-Modul dafuer sollte als Community- oder Best-Effort-App geplant werden.

### 2. Fehlende belastbare Server-Image-Publikation

- Die erwartete Docker-Hub-Seite teaspeak/server war nicht abrufbar.
- Ohne eigenen Build waere die Lieferkette zu fragil.

### 3. Architektur-Limitierung

- Upstream belegt nur amd64_stable.
- Auf ARM-Systemen ist mit Problemen zu rechnen.

### 4. Initiale Admin-Credentials

- Kritische Startinformationen erscheinen in Logs.
- Das Modul braucht dafuer einen bewusst designten Umgang.

### 5. Mehrinstanzbetrieb

- Mit festen Standardports kollidieren mehrere Instanzen auf demselben Node.
- Deshalb im MVP nur eine Instanz pro Node.

## Klare Umsetzungsempfehlung

Wenn das Projekt jetzt gestartet wird, sollte der erste Implementierungsschnitt so aussehen:

1. NS8-Modul aus ns8-kickstart erzeugen.
2. Eigenes TeaSpeak-Service-Image im Repo bauen.
3. TeaSpeak 1.5.6 fest pinnen.
4. Rootless Podman-Service mit sechs Volumes implementieren.
5. Feste Ports 9987/udp, 9987/tcp, 10101/tcp und 30303/tcp publishen.
6. Firewall-Regeln ueber node:fwadm und agent.add_public_service() verwalten.
7. Simple config.yml aus Template generieren.
8. Bootstrap-Credentials in einer dedizierten State-Datei sichern.
9. NS8-UI mit Status, Settings und About aufbauen.
10. Robot-Tests fuer Installation, Start, UI und Uninstall anlegen.

## Quellen

### NethServer 8

- https://nethserver.github.io/ns8-core/modules/new_module/
- https://nethserver.github.io/ns8-core/modules/images/
- https://nethserver.github.io/ns8-core/modules/port_allocation/
- https://nethserver.github.io/ns8-core/modules/volumes/
- https://nethserver.github.io/ns8-core/modules/network/
- https://nethserver.github.io/ns8-core/modules/systemd_units/
- https://nethserver.github.io/ns8-core/modules/rootless_rootfull/
- https://nethserver.github.io/ns8-core/modules/metadata/
- https://nethserver.github.io/ns8-core/ui/modules
- https://nethserver.github.io/ns8-core/core/firewall/
- https://github.com/NethServer/ns8-kickstart
- https://community.nethserver.org/t/building-a-nethserver-8-module-if-source-is-docker/22025

### TeaSpeak

- https://github.com/TeaSpeak/TeaDocker
- https://github.com/TeaSpeak/TeaDocker/blob/master/server/readme.md
- https://github.com/TeaSpeak/TeaDocker/blob/master/server/alpine.Dockerfile
- https://github.com/TeaSpeak/TeaDocker/blob/master/server/debian.Dockerfile
- https://github.com/TeaSpeak/TeaDocker/blob/master/server/ubuntu.Dockerfile
- https://raw.githubusercontent.com/TeaSpeak/TeaSpeak/master/default_files/config.yml
- https://repo.teaspeak.de/server/linux/amd64_stable/
- https://repo.teaspeak.de/server/linux/amd64_stable/latest
- https://teaspeak.de/