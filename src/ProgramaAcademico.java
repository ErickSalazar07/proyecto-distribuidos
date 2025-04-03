package src;

public class ProgramaAcademico {
  private String nombre;
  private Integer semestre;
  private Long numSalones;
  private Long numLaboratorios;

  public static void main(String args[]) {
    System.out.println("Proceso: \"Programa Academico\"");
  }

  public String getNombre() { return nombre; }
  public void setNombre(String nombre) { this.nombre = nombre; }
  public Integer getSemestre() { return semestre; }
  public void setSemestre(Integer semestre) { this.semestre = semestre; }
  public Long getNumSalones() { return numSalones; }
  public void setNumSalones(Long numSalones) { this.numSalones = numSalones; }
  public Long getNumLaboratorios() { return numLaboratorios; }
  public void setNumLaboratorios(Long numLaboratorios) { this.numLaboratorios = numLaboratorios; }
}
