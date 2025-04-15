package com.puj;

import org.zeromq.ZMQ;
import org.zeromq.ZContext;
import org.zeromq.SocketType;

public class Facultad {
    private String nombre;
    private Integer semestre;
    private String comunicacionServidor;

    public static void main(String[] args) {
        System.out.println("Proceso: \"Facultad\" (Servidor)");

        // Crear contexto ZeroMQ
        try (ZContext context = new ZContext()) {
            // Crear socket REP (reply)
            ZMQ.Socket socket = context.createSocket(ZMQ.REP);
            socket.bind("tcp://*:5556"); // Escucha en el puerto 5556

            System.out.println("Servidor Facultad esperando solicitudes...");

            while (!Thread.currentThread().isInterrupted()) {
                // Recibir mensaje del cliente
                String request = socket.recvStr();
                System.out.println("Solicitud recibida: " + request);

                // Lógica para responder con datos de Facultad
                String response;
                if ("nombre".equalsIgnoreCase(request)) {
                    response = "Facultad de Ingeniería";
                } else if ("semestre".equalsIgnoreCase(request)) {
                    response = "2025-1";
                } else if ("comunicacion".equalsIgnoreCase(request)) {
                    response = "ZeroMQ TCP";
                } else if ("salir".equalsIgnoreCase(request)) {
                    response = "Cerrando servidor Facultad...";
                    socket.send(response);
                    break;
                } else {
                    response = "Dato no reconocido";
                }

                // Enviar respuesta al cliente
                socket.send(response);
            }

            socket.close();
            System.out.println("Servidor Facultad finalizado.");
        }
    }
}
