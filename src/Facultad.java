package src;

public class Facultad {
  private String nombre;
  private Integer semestre;
  private String comunicacionServidor;

  public static void main(String args[]) {
    System.out.println("Proceso: \"Facultad\"");
  }

  public String getNombre() { return nombre; }
  public void setNombre(String nombre) { this.nombre = nombre; }
  public Integer getSemestre() { return semestre; }
  public void setSemestre(Integer semestre) { this.semestre = semestre; }
  public String getComunicacionServidor() { return comunicacionServidor; }
  public void setComunicacionServidor(String comunicacionServidor) { this.comunicacionServidor = comunicacionServidor; }
}
