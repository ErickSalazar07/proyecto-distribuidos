package com.puj;

import java.util.Scanner;

import org.zeromq.SocketType;
import org.zeromq.ZContext;
import org.zeromq.ZMQ;

/**
  * @brief Clase que modela un Programa Academico, el cual tiene un nombre,semestre,numero de salones, y numero de laboratorios.
*/
public class ProgramaAcademico {

  static private String nombre;
  static private String semestre;
  static private Long numSalones;
  static private Long numLaboratorios;
  static private String ipPuertoFacultad;

  public static void main(String args[]) {

    System.out.printf("%60s","BIENVENIDO AL PROCESO PROGRAMA ACADEMICO\n\n");
    Scanner sc = new Scanner(System.in);
    
    
    try(ZContext context = new ZContext()) {
      obtenerInfoPrograma(sc);
      mostrarInfoPrograma();

      ZMQ.Socket subscriber = context.createSocket(SocketType.REQ);
      subscriber.connect("tcp://" + ipPuertoFacultad);

      subscriber.send(infoProgramaString().getBytes(ZMQ.CHARSET),0);

      byte respuesta[] = subscriber.recv(0);
      System.out.printf("Respuesta de la Facultad: %s\n",
      new String(respuesta,ZMQ.CHARSET));

    } catch(Exception e) {
      System.err.printf("Error: %s\n\n",e.getMessage());
      e.printStackTrace();
    }

    sc.close();
  }

  public static void mostrarInfoPrograma() {
    System.out.printf("%50s\n\n","INFORMACION PROGRAMA ACADEMICO");
    System.out.printf("Nombre: %s\n",nombre);
    System.out.printf("Semestre: %s\n",String.valueOf(semestre));
    System.out.printf("Numero de salones: %s\n",String.valueOf(numSalones));
    System.out.printf("Numero de laboratorios: %s\n",String.valueOf(numLaboratorios));
    System.out.printf("IP y puerto de Facultad: %s\n\n", ipPuertoFacultad);
  }

  public static String infoProgramaString() {
    return "\n"
    + "Nombre: " + nombre + "\n"
    + "Semestre: " + semestre + "\n"
    + "NumSalones: " + String.valueOf(numSalones) + "\n"
    + "NumLaboratorios: " + String.valueOf(numLaboratorios) + "\n";
  }

  public static void obtenerInfoPrograma(Scanner entrada) {

    try {

      System.out.print("Dijite el nombre del programa: ");
      nombre = entrada.nextLine();
      
      System.out.print("Dijite el semestre: ");
      semestre = entrada.nextLine();

      System.out.print("Dijite el numero de salones: ");
      numSalones = Long.parseLong(entrada.nextLine());

      System.out.print("Dijite el numero de laboratorios: ");
      numLaboratorios = Long.parseLong(entrada.nextLine());

      System.out.print("Ingrese ip y puerto del servidor, con el formato (ip:puerto): ");
      ipPuertoFacultad = entrada.nextLine();
      
    } catch(NumberFormatException e) {
      System.err.println(e.getMessage());
    } catch(Exception e) {
      System.err.println(e.getMessage());
    }

  }
}
