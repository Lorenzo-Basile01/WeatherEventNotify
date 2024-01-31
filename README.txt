ISTRUZIONI PER BUILD & DEPLOYMENT

CONFIGURAZIONE TELEGRAM BOT
Per poter ricevere le notifiche in modo corretto è necessaria la configurazione di un telegram bot.
Avvia una chat con il bot @BotFather su Telegram.
Segui le istruzioni per creare un nuovo bot e ottenere il token del bot.


DOCKER
Per effettuare il build del progetto tramite docker bisogna: avere docker avviato, posizionarsi nella directory del progetto ed eseguire il comando: 'docker compose up', con tale comando si avrà una costruzione delle immagini, costruzione e avvio dei container.
Altrimenti, se si volesse effettuare il build del singolo microservizio, posizionarsi nella root specifica e digitare comando: 'docker build -t <image_name>:<image_tag>'. Infine, per creare ed avviare un container basterà digitare il seguente comando: 'docker run --name <container_name> -p <local_port>:<container_port>'.


KUBERNATES 
per deployare il progetto su kebernates bisogna:
1)In locale utilizzare Kind ed installare Kubectl
2)Posizionarsi all'interno della directory k8s e creare il comando 
	kind create cluster --config config.yaml
 per creare un cluster, in questo modo verrà creato un cluster costituito da due nodi: un control plane node e un worker node. Il cluster sarà raggiungibile tramite localhost.
3)Eseguire il comando:
 	kubectl create namespace ds
 per creare il namespace.
4)Pullare le immagini nel proprio docker-hub, questo può essere fatto attraverso i comandi "docker login" per loggari al proprio docker-hub e poi è     possibile eseguire:
	docker tag <Image ID> <cartella-docker-hub>/<docker-image-tag>
dopo questo può essere fatto 
	docker push  <cartella-docker-hub>/<docker-image-tag>
5)In seguito bisogna effettuare il deploy dei microservizi col seguente comando: 'kubectl apply -f file.yaml', nel seguente ordine:

-NGINX: ingress.yaml, effettuare prima il deploy del modulo NGINX col comando: 'kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml' e poi applicare il file di configurazione ingress.yaml;

-DB: effettuare il deploy dei database (mysql-auth.yaml, mysql-city.yaml, mysql-api.yaml, mysql-nfy.yaml, e mysql-sla.yaml), in quanto i 	microservizi, una volta avviati, proveranno subito a connettersi con essi.

-KAFKA: dopo aver deployato kafka, bisognerà creare due topic. Per fare ciò utilizzare il seguente comando, dove bisognerà specificare il nome del pod kafka e il nome del topic che si vuole creare:
	kubectl -n ds exec -it kafka-pod-name -- /bin/bash -c "/opt/kafka/bin/kafka-topics.sh --create --bootstrap-	server kafka:9095 --topic topic-name --partitions 1 --replication-factor 1"

	I due topic da creare hanno i seguenti nomi: WeatherInformations, WeatherNotification.

-MICROSERVIZI: infine, sarà possibile effettuare il deploy di tutti i microservizi (api-service.yaml, auth-service.yaml, city-service.yaml, nfy-service.yaml, prom.yaml e sla_manager.yaml).


CLIENT
All'interno del progetto sono presenti dei client.
Per entrambi i build di docker e kubernetes si possono usare i client con le porte predefinite (80).

