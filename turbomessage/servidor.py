from concurrent import futures
import grpc,threading,random,datetime,argparse

import turbomessage_pb2,turbomessage_pb2_grpc

"""
Proyecto Omega, Sis. Distribuidos @ ITAM Agosto 2023 por E. Cantu y P. Olivares.
"""

def gen_token(existentes):
    """
    Genera un token como numero aleatorio que no exista ya en 'existentes'.
    """
    while True:
        token=str(random.randint(0,1000000))
        if token not in existentes:
            return token

class ServidorTurboMessage(turbomessage_pb2_grpc.ServidorTurboMessageServicer):
    """
    Servidor de TurboMessage.
    """
    # El no. maximo de correos por bandeja 
    MAX_CAPACIDAD=5

    # El tiempo de expiracion, en horas, de los tokens de sesion
    TOKEN_EXP_HRS=1

    # No. de folio del sig. correo
    folio_correos=0

    # usuario -> lista de correos
    bandejas_entrada={}

    # usuario -> lista de correos
    bandejas_salida={}

    # usuario -> passwd
    usuarios={}

    # usuario -> token
    sesiones={}

    # Para evitar condiciones de carrera en registro de usuario
    registra_usuario_lock=threading.Lock()

    # Para evitar condiciones de carrera en asignacion de tokens
    login_token_lock=threading.Lock()

    # Para evitar condiciones de carrera en asignacion de folios a correos
    correo_folio_lock=threading.Lock()

    def registrar_usuario(self,request,context):
        """
        Registra usuario. Si el registro es exitoso, se hace login tambien.
        """

        try:

            # Pedimos lock - no queremos cuentas con el mismo usuario
            ServidorTurboMessage.registra_usuario_lock.acquire()

            # Checamos si el usuario ya existe
            if request.usuario in ServidorTurboMessage.usuarios:
                print(f'El usuario {request.usuario} ya existe')
                return turbomessage_pb2.Status(success=False,detalles="El usuario ya existe.")
            
            # Agregamos a usuarios
            ServidorTurboMessage.usuarios[request.usuario]=request.passwd

            # Y liberamos lock
            ServidorTurboMessage.registra_usuario_lock.release()

            print(f'Registro exitoso de {request.usuario}')

            # Y hacemos login de una vez
            return self.login(
                turbomessage_pb2.LoginRequest(usuario=request.usuario,passwd=request.passwd),
                context
            )
        
        except Exception as e:
            print(f'Error en registro: {e}')
            return turbomessage_pb2.Status(success=False,detalles="Error en servidor.")
        
    
    def login(self,request,context):
        """
        Hace login de usuario. Genera un token de sesion y lo guarda.
        """

        # Checamos si el usuario existe
        if request.usuario not in ServidorTurboMessage.usuarios:
            return turbomessage_pb2.Status(success=False,detalles="El usuario no existe.")
        
        try:
            
            # Pedimos lock - no queremos sesiones con tokens repetidos
            ServidorTurboMessage.login_token_lock.acquire()

            # Generamos y agregamos token a sesiones
            token=gen_token(ServidorTurboMessage.sesiones.values())
            ServidorTurboMessage.sesiones[request.usuario]=(token,datetime.datetime.now())

            # Liberamos lock
            ServidorTurboMessage.login_token_lock.release()

            print(f'Login exitoso de {request.usuario}')

            return turbomessage_pb2.Status(success=True,detalles=token)
        
        except Exception as e:
            print(f'Error en login: {e}')
            return turbomessage_pb2.Status(success=False,detalles="Error en servidor.")
        
    def enviar_mensaje(self,request,context):
        """
        Envia un correo. Se checa que el usuario tenga permisos y espacio para mandarlo,
        que el destinatario exista y tenga espacio para recibirlo.
        """
        MAX_CAPACIDAD=ServidorTurboMessage.MAX_CAPACIDAD

        # Checamos que el usuario tenga una sesion
        if not self.validar_token(request.usuario,request.token):
            return turbomessage_pb2.Status(success=False,detalles="Inicia antes de hacer operacion.")
        
        correo=request.correo

        # Checamos que 'de' del correo coincida con el usuario
        if correo.desde!=request.usuario:
            return turbomessage_pb2.Status(success=False,detalles="Usuario y campo de emisor deben coincidir.")
        
        # Checamos que 'a' del correo exista
        if correo.a not in ServidorTurboMessage.usuarios:
            return turbomessage_pb2.Status(success=False,detalles="Usuario destinatario no existe.")

        # Checamos si bandeja de salida tiene espacio y la creamos si no existe
        ServidorTurboMessage.bandejas_salida[correo.desde]=ServidorTurboMessage.bandejas_salida.get(correo.desde,{})
        if len(ServidorTurboMessage.bandejas_salida[correo.desde])>=MAX_CAPACIDAD:
            return turbomessage_pb2.Status(success=False,detalles="Bandeja de salida llena.")
        
        # Checamos si bandeja de entrada tiene espacio y la creamos si no existe
        ServidorTurboMessage.bandejas_entrada[correo.a]=ServidorTurboMessage.bandejas_entrada.get(correo.a,{})
        if len(ServidorTurboMessage.bandejas_entrada[correo.a])>=MAX_CAPACIDAD:
            return turbomessage_pb2.Status(success=False,detalles="Bandeja de entrada de receptor llena.")
        
       
        # Pedimos lock - no queremos correos con el mismo folio
        ServidorTurboMessage.correo_folio_lock.acquire()

        # Asignamos folio al correo y incrementamos folio
        correo.id=ServidorTurboMessage.folio_correos
        ServidorTurboMessage.folio_correos+=1

        # Liberamos lock
        ServidorTurboMessage.correo_folio_lock.release()

        # Aseguramos que este marcado como no leido
        correo.leido=False

        # Almacenar en bandeja de salida
        ServidorTurboMessage.bandejas_salida[correo.desde][correo.id]=correo

        # Almacenar en bandeja de entrada correspondiente
        ServidorTurboMessage.bandejas_entrada[correo.a][correo.id]=correo

        print(f'Envio de correo {correo.id} exitoso.')

        return turbomessage_pb2.Status(success=True)
    
    def borrar_mensaje(self,request,context):
        """
        Se borra dado el folio y bandeja del usuario correspondiente.
        """

        # Checamos que el usuario tenga una sesion
        if not self.validar_token(request.usuario,request.token):
            return turbomessage_pb2.Status(success=False,detalles="Inicia antes de hacer operacion.")
        
        bandeja=ServidorTurboMessage.bandejas_salida[request.usuario] if request.bandeja=='salida' else ServidorTurboMessage.bandejas_entrada[request.usuario]
        
        # Checamos si existe el mensaje en la bandeja
        if request.correo_id not in bandeja:
            return turbomessage_pb2.Status(success=False,detalles="No existe ese correo en tu bandeja.")
        
        # Borramos
        del bandeja[request.correo_id]

        print(f'Eliminacion de correo {request.correo_id} exitoso.')

        return turbomessage_pb2.Status(success=True)
    

    def marcar_leido(self,request,context):
        """
        Se marca como leido el correo dado el folio y bandeja del usuario correspondiente.
        """

        # Checamos que el usuario tenga una sesion
        if not self.validar_token(request.usuario,request.token):
            return turbomessage_pb2.Status(success=False,detalles="Inicia antes de hacer operacion.")
        
        # Solo se pueden marcar como leidos mensajes en la bandeja de entrada
        bandeja=ServidorTurboMessage.bandejas_entrada
        
        # Checamos si existe el mensaje en la bandeja
        if request.usuario not in bandeja or request.correo_id not in bandeja[request.usuario]:
            return turbomessage_pb2.Status(success=False,detalles="No existe ese correo en tu bandeja de entrada.")
        
        # Marcamos como leido
        bandeja[request.usuario][request.correo_id].leido=True
        return turbomessage_pb2.Status(success=True)
    

    def get_bandeja(self,request,context):
        """
        Regresa la bandeja de un usuario como una lista de correos.
        """

        # Checamos que el usuario tenga una sesion
        if not self.validar_token(request.usuario,request.token):
            return turbomessage_pb2.Bandeja()
        
 
        tipo_bandeja=ServidorTurboMessage.bandejas_salida if request.bandeja=='salida' else ServidorTurboMessage.bandejas_entrada
        correos=tipo_bandeja.get(request.usuario,{})
        correos=list(correos.values())
        return turbomessage_pb2.Bandeja(correos=correos)
        

    def validar_token(self,usuario,token):
        """
        Checa si el usuario tiene una sesion activa y regresa un booleano.
        Si el token de sesion no ha expirado se renueva.
        """

        # Checamos que el usuario tenga una sesion
        if usuario not in ServidorTurboMessage.sesiones:
            return False
        
        token_guardado,ultima_actividad=ServidorTurboMessage.sesiones[usuario]

        # Checamos que los tokens coincidan
        if token!=token_guardado:
            return False
        
        # Calculamos el no. de horas que han pasado de la ultima actividad
        hrs_desde_ultima_actividad=(datetime.datetime.now() - ultima_actividad).seconds/3600

        # Si es mayor que el limite, el token esta expirado
        if hrs_desde_ultima_actividad>ServidorTurboMessage.TOKEN_EXP_HRS:
            return False
        
        else:
            # Actualizamos y regresamos cierto
            ServidorTurboMessage.sesiones[usuario]=(token_guardado,datetime.datetime.now())
            return True


def ofrece_servicios(puerto):
    """
    Lanza el servidor de forma concurrente en el puerto especificado.
    """
    servidor = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    turbomessage_pb2_grpc.add_ServidorTurboMessageServicer_to_server(ServidorTurboMessage(), servidor)
    servidor.add_insecure_port("[::]:" + puerto)
    servidor.start()
    servidor.wait_for_termination()


if __name__ == "__main__":

    # Parseamos el puerto en el que lanzar el servidor
    parser=argparse.ArgumentParser(
        prog='Servidor TurboMessage',
        description='Hostea el servicio TurboMessage',
        epilog='Proyecto Omega, Sis. Distribuidos @ ITAM Agosto 2023 por E. Cantu y P. Olivares'
    )
    parser.add_argument('-p','--puerto',default='50052',help='El puerto en el que lanzar el servidor TurboMessage')
    args=vars(parser.parse_args())

    # Y lanzamos el servidor
    print("Lanzando servidor ...")
    ofrece_servicios(args['puerto'])