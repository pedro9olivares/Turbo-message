import grpc,sys,argparse,os
import turbomessage_pb2,turbomessage_pb2_grpc


"""
Proyecto Omega, Sis. Distribuidos @ ITAM Agosto 2023 por E. Cantu y P. Olivares.
"""

def clear_screen():
   # for windows
   if os.name == 'nt':
      _ = os.system('cls')

   # for mac and linux
   else:
      _ = os.system('clear')

class Cliente():
    """
    Cliente con interface de terminal para usar TurboMessage.
    """

    def __init__(self,ip,puerto):
        """
        Establece canal a servidor con ip y puerto, inicializa variables de sesion,
        y despliega el menu de operaciones.
        """
        # Abrimos canal a servidor
        try:
            self.canal=grpc.insecure_channel(f'{ip}:{puerto}')
            self.stub=turbomessage_pb2_grpc.ServidorTurboMessageStub(self.canal)
        except:
            print('No se pudo establecer canal con servidor. Intenta de nuevo.')
            sys.exit(1)

        # El usuario y token de sesion
        self.usuario=None
        self.token=None

        # Caches de las bandejas de entrada y salida
        self.bandeja_entrada=[]
        self.bandeja_salida=[]

        # Ultimo mensaje de exito/error
        self.status=None

        # Desplegamos menu de operaciones hasta que el usuario seleccione salir
        self.menu_operaciones()

    def salir(self):
        """
        Cierra el canal y termina el programa.
        """
        self.canal.close()
        sys.exit(0)

    def registro(self):
        """
        Pregunta por info y registra a usuario con servidor.
        """
        
        print('Iniciando registro')

        # Parseamos inputs
        usuario=input('Ingresa tu nombre de usuario: ').strip()
        passwd=input('Ingresa tu contraseña: ').strip()
        passwd_conf=input('Confirma tu contraseña: ').strip()
        if passwd!=passwd_conf:
            print(f'Contraseñas no coinciden. Intenta de nuevo.')

        else: 
            # Intentamos registrar
            status=self.stub.registrar_usuario(
                turbomessage_pb2.LoginRequest(usuario=usuario,passwd=passwd)
            )

            self.status=(f'Error: {status.detalles}. Intenta de nuevo.' if not status.success else 'Registro exitoso.')

            
            # Guardamos usuario y token
            self.usuario=usuario
            self.token=status.detalles

    def login(self):
        """
        Pregunta por credeciales y hace login con servidor.
        """

        # Parseamos inputs
        usuario=input('Ingresa tu nombre de usuario: ').strip()
        passwd=input('Ingresa tu contraseña: ').strip()

        # Intentamos hacer login
        status=self.stub.login(
            turbomessage_pb2.LoginRequest(usuario=usuario,passwd=passwd)
        )

        self.status=(f'Error: {status.detalles}. Intenta de nuevo.' if not status.success else 'Sesion iniciada.')
        
        # Guardamos usuario y token
        if status.success:
            self.usuario=usuario
            self.token=status.detalles

    def _get_bandeja(self,tipo,despliega=True):
        """
        Hace fetch de la bandeja tipo (entrada/salida) con el servidor y la despliega.
        """

        bandeja=self.stub.get_bandeja(
            turbomessage_pb2.GetBandejaRequest(
                usuario=self.usuario,
                token=self.token,
                bandeja=tipo
            )
        )

        if despliega:
            print(f'\nBandeja de {tipo}:\n')

            if bandeja.correos:
                for correo in bandeja.correos:
                    asunto=correo.contenido.split('-----')[0]
                    de_a=f'A: {correo.a} 'if 'salida' in tipo else f'De: {correo.desde}'
                    print(f'\tFolio: {correo.id} Leido: {"✓" if correo.leido else "-"} {de_a} Asunto: {asunto}')
            else:
                print('\tBuzon vacio.')
        
        return bandeja.correos
    
    def enviar(self):
        """
        Recompila mensaje y lo envia.
        """

        print('Enviar Mensaje')
        a=input('Para usuario: ').strip()
        asunto=input('Asunto: ').strip()
        cuerpo=input('Cuerpo: \n').strip()
        contenido=asunto+'-----'+cuerpo

        correo=turbomessage_pb2.Correo(desde=self.usuario,a=a,contenido=contenido)
        
        status=self.stub.enviar_mensaje(
            turbomessage_pb2.EnviarMensajeRequest(
                usuario=self.usuario,
                token=self.token,
                correo=correo
            )
        )
        self.status=(f'Error: {status.detalles} Intenta de nuevo.' if not status.success else 'Correo enviado.')


    def _busca_correo_en_bandejas(self,folio):
        """
        Busca correo con id==folio en bandejas de entrada y salida.
        Regresa el correo si lo encuentra, junto con la bandeja en la que estaba.
        """
        correo,bandeja=None,None

        # Checamos primero la de entrada
        for c in self.bandeja_entrada:
            if c.id==folio:
                correo=c
                bandeja='entrada'
                break

        if correo is None:
            # Y si no lo hemos encontrado, despues el de salida
            for c in self.bandeja_salida:
                if c.id==folio:
                    correo=c
                    bandeja='salida'
                    break 
        
        return correo,bandeja

    def borrar(self):
        """
        Pregunta por folio y borra con el servidor el correo correspondiente.
        """

        # Preguntamos por folio
        try:
            folio=int(input(f'Ingresa el folio del correo a borrar: ').strip())
        except:
            self.status=('Ingresa un folio valido. Intenta de nuevo.')
            return None

        # Buscamos el correo
        correo,bandeja=self._busca_correo_en_bandejas(folio)
        if correo is None or bandeja is None:
            self.status=('Folio no encontrado. Intenta de nuevo.')
        
        else:
            # E intentamos borrar con el servidor
            status=self.stub.borrar_mensaje(
                turbomessage_pb2.MensajeActionRequest(
                    usuario=self.usuario,
                    token=self.token,
                    correo_id=folio,
                    bandeja=bandeja
                )
            )
            self.status=(f'Error: {status.detalles} Intenta de nuevo.' if not status.success else 'Correo borrado.')


    def leer(self):
        """
        Pregunta por folio, despliega el correo correspondiente y marca como leido
        con el servidor.
        """

        # Preguntamos por folio
        try:
            folio=int(input(f'Ingresa el folio del correo a leer: ').strip())
        except:
            self.status=('Ingresa un folio valido. Intenta de nuevo.')
            return None

        # Encuentra el correo con el folio
        correo,bandeja=self._busca_correo_en_bandejas(folio)

        # Marcamos como leido en el servidor
        if correo is None or bandeja is None:
            self.status=('Folio no encontrado. Intenta de nuevo.')

        elif bandeja=='entrada' and not correo.leido:
            # Si esta en el buzon de entrada y no ha sido marcado como leido
            # lo marcamos como leido con el servidor
            status=self.stub.marcar_leido(
                turbomessage_pb2.MensajeActionRequest(
                        usuario=self.usuario,
                        token=self.token,
                        correo_id=folio,
                        bandeja=bandeja
                )
            )
            self.status=(f'Error: {status.detalles} Intenta de nuevo.' if not status.success else 'Correo marcado como leido.')
        
        elif bandeja=='salida':
            self.status=('Correo leido.')

        # Desplegamos
        if correo is not None:
            print('='*100)
            print(f'\n\n\tFolio: {correo.id} De: {correo.desde}')
            print(f'\n\tAsunto: {correo.contenido.split("-----")[0]}')
            print(f'\n\t\t{correo.contenido.split("-----")[1]}\n')
            print('='*100)

        
    def info_screen(self):
        """
        La informacion que se despliega en la parte superior del menu principal.
        Incluye mensaje de error/exito, nombre de usuario y bandejas de entrada y salida.
        """
        print('\nTurboMessage Cliente')

        # Ultimo mensaje de error/exito.
        if self.status:
            print(f'\nFeedback: {self.status}')

        # Refrescamos bandejas
        if self.usuario:
            print(f'\nUsuario: {self.usuario}')
            self.bandeja_entrada=self._get_bandeja('entrada')
            self.bandeja_salida=self._get_bandeja('salida')


    def menu_operaciones(self):
        """
        Menu principal. Despliega informacion (con info_screen), las opciones
        disponibles y ejecuta la opcion que selecciona el usuario. Termina hasta
        que el usuario seleccione la opcion 'Salir'.
        """

        opciones_sin_sesion={
            '0':('Salir',self.salir),
            '1':('Login',self.login),
            '2':('Registro',self.registro),
        }

        opciones_con_sesion={
            '0':('Salir',self.salir),
            '1':('Mandar Mensaje',self.enviar),
            '2':('Leer Mensaje',self.leer),
            '3':('Borrar Mensaje',self.borrar),
            '4':('Refresh',self.menu_operaciones),
        }

        while True:

            # Borramos consola solo si la ultima accion no fue ver correo
            if (self.status and 'leido' not in self.status) or self.status is None:
                clear_screen()#print("\033[H\033[J", end="")

            # Desplegamos informacion
            self.info_screen()

            # Desplegamos opciones
            opciones=opciones_con_sesion if self.token else opciones_sin_sesion

            print('\nOperaciones disponibles:\n')
            for opcion,(texto,_) in opciones.items():
                print(f'\t({opcion}) {texto}')
            print()


            opcion=input('Ingresa el no. de operacion a realizar: ').strip()
            if opcion in opciones:
                print('\n')
                opciones[opcion][1]()
            else:
                print('Opcion no valida. Intenta de nuevo.') 


if __name__=='__main__':

    # Parseamos la direccion IP y puerto del servidor
    parser=argparse.ArgumentParser(
        prog='Cliente TurboMessage',
        description='Consulta y administra tus correos TurboMessage',
        epilog='Proyecto Omega, Sis. Distribuidos @ ITAM Agosto 2023 por E. Cantu y P. Olivares'
    )
    parser.add_argument('-i','--ip',default='localhost',help='La direccion IPv4 del servidor TurboMessage.')
    parser.add_argument('-p','--puerto',default='50052',help='El puerto en el que escucha el servidor TurboMessage')
    args=vars(parser.parse_args())

    # E inicializamos el cliente
    c=Cliente(args['ip'],args['puerto'])
    