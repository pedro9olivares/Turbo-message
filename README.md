# Proyecto $\omega$ - Sistemas Distribuidos

Implementación en Python de un servicio tipo email usando [gRPC](https://grpc.io/) y [Protocol Buffers](https://protobuf.dev/). 

Elaborado por Emilio Cantú y Pedro Olivares para la clase de Sistemas Distribuidos - ITAM Primavera 2023.

## Contenido
- [Cómo usar](#cómo-usar)
- [Protos](#protos)
- [Servidor](#servidor)
- [Cliente](#cliente)

## Cómo usar
1. Clona este repositorio
2. Instala [Python 3](https://www.python.org/downloads/)
3. Instala los paquetes necesarios con pip: `pip3 install -r requirements.txt`
4. Lanza el servidor: `python3 turbomessage/servidor.py [puerto]`
5. Lanza el cliente con la dirección IP y puerto del servidor: `python3 turbomessage/cliente.py [ip] [puerto]`

Nota: Si deseas volver a compilar los archivos `.proto` puedes correr el comando (**dentro de** la carpeta `protos/`)
```
python3 -m grpc_tools.protoc -I. --python_out=. --pyi_out=. --grpc_python_out=. *.proto
```
y copiar los archivos generados a la carpeta `turbomessage/`.

## Protos
Definición de los rpc's a implementar usando [Protocol Buffers](https://protobuf.dev/).

Para que un servidor pueda implementar el servicio de emails se requiere que este sea capaz de administrar usuarios y bandejas de entrada/salida, enviar correos y actuar sobre los correos. Por lo tanto, se definen los siguiente procedimientos remotos:

**Administración de usuarios**

- `registrar_usuario (LoginRequest) returns (Status)`
- `login (LoginRequest) returns (Status)`,

donde el mensaje `LoginRequest` tiene como atributos un usuario y contraseña, mientras que el mensaje `Status` tiene como atributos un booleano que representa el éxito o fracaso de la llamda al procedimiento y una string con los detalles.

**Bandejas de entrada y salida**

- `get_bandeja (GetBandejaRequest) returns (Bandeja)`,

donde el mensaje `GetBandejaRequest` tiene como atributos un usuario, un token y una string para especificar si se quiere recuperar la bandeja de entrada o la de salida. El mensaje `Bandeja` contiene una colección (via un `repeated`) de mensajes tipo `Correo`, los cuales tienen atributos de id, emisor, receptor, si fue leído, y el contenido del mismo.

**Envío de correos**

- `enviar_mensaje (EnviarMensajeRequest) returns (Status)`,

donde el mensaje `EnviarMensajeRequest` tiene como atributos al usuario que desea enviar el correo, su token y un mensaje tipo `Correo` definido como arriba. Igualmente, regresa el mensaje `Status` definido como arriba.

**Actuación sobre correos**

- `borrar_mensaje (MensajeActionRequest) returns (Status)`
- `marcar_leido (MensajeActionRequest) returns (Status)`,

donde el mensaje `MensajeActionRequest` tiene como atributos al usuario que desea borrar o leer un correo, su token, el id del correo a interactuar, y la bandeja en donde se encuentra el correo (entrada o salida).  Igualmente, regresa el mensaje `Status` definido como arriba.

## Servidor

Servidor que implementa toda la funcionalidad del servico de emails. El servidor escucha en el puerto `50052` por default, modificable al correr el servidor desde terminal. 

El servidor tiene una función de uso interno `gen_tokens` para asignar tokens de sesión a cada usuario que lo consuma. Se especifica que el número máximo de correos por bandeja de cada usuario sea 5 y que cada token de sesión tenga una duración máxima de una hora. A su vez, el servidor lleva un registro interno de todos lo correos enviados asignándoles un folio numérico consecutivo.

El servidor maneja la información de las bandejas, usuarios y sesiones utilizando diccionarios, y utiliza locks del módulo [threading](https://docs.python.org/3/library/threading.html#thread-objects) de Python para evitar condiciones de carrera al registrar usuarios, al asignar tokens (lo que restringe a que solo se pueda iniciar sesión en una sola máquina), y al asignar folios a correos. 

Los detalles de implementación de los métodos del servidor, que se sirven del **stub** y la infraestructura generada por [gRPC](https://grpc.io/), son los siguientes: 
- `registrar_usuario`: si el registro es exitoso, se hace login también; 
- `login`: para que el usuario adquiera un token de sesión protegido ante condiciones de carrera; 
- `enviar_mensaje`: si el usuario existe y el destino es un usuario que también existe, se manda el correo y se almacena en las bandejas de entrada y salida del emisor y receptor solo si estas aún tienen capacidad, y el servidor asigna un folio protegido ante condiciones de carrera al correo enviado; 
- `borrar_mensaje`: solo si el usuario existe y el mensaje a borrar existe en la bandeja seleccionada;  
- `marcar_leido`: solo si el correo existe en la bandeja de entrada del usuario;  
- `get_bandeja`: recupera la bandeja de correos de un usuario como una lista de correos; 
- `ofrece_servicios`: levanta el servidor.

<img width="664" alt="image" src="https://user-images.githubusercontent.com/61219691/235570084-bb2cec73-480c-4267-82f6-fe52a355da5b.png">


## Cliente
El cliente implementa una interfaz en terminal para el uso del servicio de emails. Es necesario indicar la ip y puerto del servidor al que se accederá. La conexión se hace via un `insecure_channel` de [gRPC](https://grpc.io/). 

La interfaz en terminal contiene las opciones necesarias para interactuar con el servidor y hacer uso de los rpc's definidos más arriba, cuya implementación se logra via el uso del **stub** generado. 

Adicionalmente, el cliente implementa los métodos de `_busca_correo_en_bandeja` (para desplegar los correos del cliente), `leer` (para desplegar el contenido de un correo) e `info_screen` y `menu_operaciones` (para la parte "gráfica" de la interfaz en terminal).

<img width="681" alt="image" src="https://user-images.githubusercontent.com/61219691/235570795-eeb627ca-5859-4def-bbdf-6ea9dbc8bdde.png">

## Conclusiones
En resumen, este proyecto nos permitió aprender a implementar un servicio realista mediante el uso de Python y gRPC, con la ventaja de poder ser compatible con cualquier otro lenguaje que soporte este protocolo. Además, consideramos que existen oportunidades de mejora en cuanto a aumentar el límite de las bandejas, mejorar la interfaz y sofisticar la base de datos del servidor. A pesar de ello, esta experiencia nos permitió comprender la conveniencia de utilizar gRPC y protobufs en la construcción de servicios distribuidos, lo que sin duda nos será de gran utilidad en futuros proyectos.

