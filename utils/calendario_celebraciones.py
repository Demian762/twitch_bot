from __future__ import annotations

from datetime import date, timedelta

_MESES = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
    5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
    9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre",
}


def _pascua(year: int) -> date:
    """Algoritmo de Meeus/Jones/Butcher para calcular la fecha de Pascua."""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def _nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    """Devuelve el n-ésimo día de la semana (0=lun … 6=dom) de un mes."""
    first = date(year, month, 1)
    delta = (weekday - first.weekday()) % 7
    return first + timedelta(days=delta + 7 * (n - 1))


# Fechas fijas: key = "MM-DD", value = lista de celebraciones.
# Fuentes: kalender-365.de (días ONU), acuarela.wordpress.com (días profesionales arg.),
# suteba.org.ar (efemérides históricas arg.) y conocimiento general.
CELEBRACIONES: dict[str, list[str]] = {
    # ── ENERO ──────────────────────────────────────────────────────────────────
    "01-01": ["Año Nuevo"],
    "01-03": ["Usurpación de las Islas Malvinas (1833)"],
    "01-04": ["Día Mundial del Braille"],
    "01-05": ["Día del Fotógrafo"],
    "01-06": ["Día de Reyes / Epifanía"],
    "01-07": ["Inicio de la Semana Trágica (1919)"],
    "01-10": ["Día del Trabajador Impositivo (AFIP/DGI)"],
    "01-19": ["Día del Cervecero"],
    "01-23": ["Día por el Derecho a las Vacaciones"],
    "01-24": ["Día Internacional de la Educación", "Día del Periodista Gráfico"],
    "01-25": ["Día Nacional de los Reporteros Gráficos"],
    "01-27": ["Día Internacional en Memoria de las Víctimas del Holocausto"],
    "01-31": ["Inauguración de la Asamblea del Año XIII (1813)"],
    # ── FEBRERO ────────────────────────────────────────────────────────────────
    "02-04": ["Día Internacional de la Fraternidad Humana", "Día del Guardavidas"],
    "02-06": ["Día Internacional de Tolerancia Cero con la MGF"],
    "02-10": ["Día Mundial de las Legumbres"],
    "02-11": ["Día Internacional de la Mujer y la Niña en la Ciencia"],
    "02-14": ["Día de San Valentín / Día de los Enamorados"],
    "02-15": ["Día del Redactor Publicitario"],
    "02-20": ["Día Mundial de la Justicia Social"],
    "02-21": ["Día Internacional de la Lengua Materna"],
    "02-22": ["Día de la Antártida Argentina"],
    "02-25": ["Inauguración de la Represa Binacional Yaciretá"],
    "02-27": ["Creación de la Bandera Nacional Argentina (1812)"],
    # ── MARZO ──────────────────────────────────────────────────────────────────
    "03-01": ["Día de la Discriminación Cero", "Día del Trabajador del Transporte"],
    "03-03": ["Día Mundial de la Vida Silvestre"],
    "03-06": ["Día del Escultor"],
    "03-08": ["Día Internacional de la Mujer"],
    "03-12": ["Aprobación del Escudo Nacional Argentino (1813)"],
    "03-14": ["Día de las Escuelas de Frontera"],
    "03-16": ["Inauguración de la Biblioteca Pública de Buenos Aires (1812)"],
    "03-20": ["Día Internacional de la Felicidad"],
    "03-21": [
        "Día Internacional para la Eliminación de la Discriminación Racial",
        "Día Mundial de la Poesía",
        "Día Internacional del Bosque",
        "Día Mundial del Síndrome de Down",
    ],
    "03-22": ["Día Mundial del Agua"],
    "03-23": ["Día Meteorológico Mundial"],
    "03-24": [
        "Día Nacional de la Memoria por la Verdad y la Justicia",
        "Día Mundial contra la Tuberculosis",
        "Día del Diplomático",
    ],
    "03-25": [
        "Día Internacional de Conmemoración de las Víctimas de la Esclavitud",
        "Aniversario del asesinato de Rodolfo Walsh (1977)",
    ],
    "03-27": ["Día Mundial del Teatro", "Día del Aeronáutico"],
    "03-30": ["Jornada de lucha contra la dictadura (1982)"],
    # ── ABRIL ──────────────────────────────────────────────────────────────────
    "04-02": [
        "Día del Veterano y de los Caídos en la Guerra de Malvinas",
        "Día Mundial de Concienciación sobre el Autismo",
    ],
    "04-03": ["Día del Modelo"],
    "04-04": [
        "Día Internacional de Concienciación sobre Minas",
        "Asesinato del maestro Carlos Fuentealba (2007)",
    ],
    "04-05": ["Día Internacional de la Consciencia"],
    "04-06": ["Día Internacional del Deporte para el Desarrollo y la Paz"],
    "04-07": ["Día Mundial de la Salud"],
    "04-09": ["Día del Investigador Científico"],
    "04-12": ["Día Internacional del Vuelo Humano en el Espacio", "Día del Decorador"],
    "04-13": ["Día del Kinesiólogo"],
    "04-14": ["Día de las Américas"],
    "04-18": ["Día Internacional de los Monumentos y Sitios"],
    "04-19": ["Día del Aborigen Americano / Día de los Pueblos Originarios"],
    "04-21": ["Día Mundial de la Creatividad y la Innovación", "Día del Traductor"],
    "04-22": ["Día de la Tierra"],
    "04-23": ["Día Mundial del Libro y del Derecho de Autor"],
    "04-24": ["Día Internacional del Multilateralismo y la Diplomacia para la Paz"],
    "04-25": ["Día Internacional del Delegado", "Día Mundial contra la Malaria"],
    "04-26": ["Día Mundial de la Propiedad Intelectual", "Día del Librero"],
    "04-27": ["Día del Agente de Viajes"],
    "04-28": ["Día Mundial de la Seguridad y la Salud en el Trabajo"],
    "04-29": ["Día Internacional de la Danza"],
    "04-30": ["Día Internacional del Jazz"],
    # ── MAYO ───────────────────────────────────────────────────────────────────
    "05-01": ["Día Internacional del Trabajador"],
    "05-02": ["Día Mundial del Atún"],
    "05-03": ["Día Mundial de la Libertad de Prensa"],
    "05-06": ["Día del Taxista"],
    "05-07": ["Día del Trabajador Gráfico", "Nacimiento de Eva María Duarte de Perón (1919)"],
    "05-08": ["Día Mundial de la Cruz Roja"],
    "05-10": ["Día de los Medios de Comunicación"],
    "05-11": ["Día del Himno Nacional Argentino"],
    "05-12": ["Día Internacional de la Enfermería", "Día de la Enfermera"],
    "05-15": ["Día Internacional de las Familias"],
    "05-16": ["Día Internacional de Convivencia en Paz", "Día Internacional de la Luz"],
    "05-17": ["Día Mundial de las Telecomunicaciones", "Día de la Armada Argentina"],
    "05-18": ["Día de la Escarapela Argentina"],
    "05-19": ["Conmemoración de la muerte de José Martí (1895)"],
    "05-20": ["Día Mundial de las Abejas", "Día del Futbolista Argentino"],
    "05-21": ["Día Mundial del Té", "Día Mundial para la Diversidad Cultural"],
    "05-22": ["Día Internacional de la Diversidad Biológica"],
    "05-23": ["Día de los Trabajadores de la Educación"],
    "05-25": ["Día de la Revolución de Mayo / Día de la Patria"],
    "05-26": ["Día del Visitador Médico"],
    "05-27": ["Día del Marketing"],
    "05-28": ["Día de los Jardines de Infantes y Maestros Jardineros"],
    "05-29": ["Día Internacional de los Cascos Azules de la ONU", "El Cordobazo (1969)"],
    "05-31": ["Día Mundial Sin Tabaco"],
    # ── JUNIO ──────────────────────────────────────────────────────────────────
    "06-01": ["Día Global de los Padres (ONU)", "Primer Paro Docente a la Dictadura (1977)"],
    "06-02": ["Día del Graduado en Ciencias Económicas", "Día del Bombero Voluntario"],
    "06-03": ["Día Mundial de la Bicicleta", "Día de la Formación Profesional"],
    "06-04": ["Día Internacional de los Niños Víctimas Inocentes de Agresión"],
    "06-05": ["Día Mundial del Medio Ambiente"],
    "06-07": ["Día del Periodista Argentino", "Día Mundial de la Inocuidad de los Alimentos"],
    "06-08": ["Día Mundial de los Océanos"],
    "06-10": ["Día de la Afirmación de los Derechos Argentinos sobre las Islas Malvinas"],
    "06-12": ["Día Mundial contra el Trabajo Infantil"],
    "06-13": ["Día del Escritor Argentino", "Día Internacional de Concienciación sobre el Albinismo"],
    "06-14": ["Día Mundial del Donante de Sangre"],
    "06-15": ["Día del Libro Argentino", "Día del Bioquímico"],
    "06-16": ["Día del Ingeniero Argentino", "Bombardeo a Plaza de Mayo (1955)"],
    "06-17": ["Día Mundial de Lucha contra la Desertificación y la Sequía", "Día Nacional de la Libertad Latinoamericana"],
    "06-18": ["Día del Empresario", "Día de la Gastronomía Sostenible"],
    "06-19": ["Día del Bancario / Empleado Bancario", "Día Internacional para la Eliminación de la Violencia Sexual en Conflictos"],
    "06-20": ["Día de la Bandera Argentina", "Día Mundial del Refugiado", "Paso a la Inmortalidad del General Manuel Belgrano"],
    "06-21": ["Año Nuevo de los Pueblos Originarios / Inti Raymi", "Día Internacional del Yoga", "Solsticio de invierno"],
    "06-23": ["Día del Servicio Público de las Naciones Unidas", "Día Internacional de las Viudas"],
    "06-25": ["Día del Marino / Gente de Mar"],
    "06-26": [
        "Día Internacional contra el Abuso de Drogas y el Tráfico Ilícito",
        "Día de las Naciones Unidas en Apoyo a las Víctimas de la Tortura",
        "Asesinato de Darío Santillán y Maximiliano Kosteki (2002)",
    ],
    "06-27": ["Día de las Micro, Pequeñas y Medianas Empresas"],
    "06-29": ["Día Internacional de los Trópicos"],
    "06-30": ["Día Internacional de los Asteroides", "Día Internacional del Parlamentarismo"],
    # ── JULIO ──────────────────────────────────────────────────────────────────
    "07-01": ["Fallecimiento de Juan Domingo Perón (1974)"],
    "07-02": ["Día del Editor de Revistas"],
    "07-03": ["Día del Locutor Argentino", "Fallecimiento de Hipólito Yrigoyen (1933)"],
    "07-05": ["Día de la Empleada de Casa de Familia"],
    "07-08": ["Día del Inventor", "Promulgación de la Ley 1420 de Educación Común (1884)"],
    "07-09": ["Día de la Independencia Argentina"],
    "07-11": ["Día Mundial de la Población"],
    "07-12": ["Día de las Heroínas y Mártires de la Independencia Argentina"],
    "07-15": ["Día Mundial de las Competencias Juveniles"],
    "07-18": ["Día Internacional Nelson Mandela", "Atentado a la AMIA (1994)"],
    "07-20": ["Día del Amigo (Argentina)"],
    "07-21": ["Día del Derecho"],
    "07-26": ["Paso a la Inmortalidad de María Eva Duarte de Perón / Evita (1952)"],
    "07-28": ["Día Mundial contra la Hepatitis"],
    "07-29": ["La Noche de los Bastones Largos (1966)"],
    "07-30": ["Día Internacional de la Amistad (ONU)", "Día Mundial contra la Trata de Personas"],
    # ── AGOSTO ─────────────────────────────────────────────────────────────────
    "08-01": ["Día Nacional en Memoria de Santiago Maldonado"],
    "08-02": ["Día del Gastronómico"],
    "08-06": ["Día del Ingeniero Agrónomo", "Día del Médico Veterinario"],
    "08-09": ["Día Internacional de los Pueblos Indígenas"],
    "08-10": ["Marcha Grande por el Trabajo y la Justicia Social"],
    "08-11": ["Día del Dentista"],
    "08-12": [
        "Día Internacional de la Juventud",
        "Día del Trabajador de la Televisión",
        "Reconquista de Buenos Aires (1806)",
        "Inauguración de la Universidad de Buenos Aires (1821)",
    ],
    "08-14": ["Día del Empleado Judicial"],
    "08-17": ["Paso a la Inmortalidad del General José de San Martín"],
    "08-19": ["Día Mundial Humanitario"],
    "08-20": ["Día del Despachante de Aduana"],
    "08-21": ["Día Internacional de Conmemoración y Homenaje a las Víctimas del Terrorismo"],
    "08-22": ["Aniversario de la Masacre de Trelew (1972)", "Día Mundial del Folklore"],
    "08-23": [
        "Día Internacional para el Recuerdo de la Trata de Esclavos y de su Abolición",
        "Desaparición de Felipe Vallese (1962)",
    ],
    "08-25": ["Día del Peluquero y la Peluquera"],
    "08-26": ["Día del Actor / Día de la Actuación", "Día de la Medicina Argentina"],
    "08-29": ["Día del Abogado Argentino", "Día Internacional contra los Ensayos Nucleares"],
    "08-30": ["Día Internacional de los Detenidos-Desaparecidos"],
    "08-31": ["Día de la Obstétrica / Partera"],
    # ── SEPTIEMBRE ─────────────────────────────────────────────────────────────
    "09-02": ["Día de la Industria Argentina"],
    "09-04": ["Día de la Secretaria / Secretario", "Día del Inmigrante (Argentina)", "Día Nacional de la Historieta Argentina"],
    "09-05": ["Día Internacional de la Caridad"],
    "09-07": ["Fundación de la Biblioteca Pública de Buenos Aires (1810)"],
    "09-08": ["Día Internacional de la Alfabetización"],
    "09-10": ["Día Mundial para la Prevención del Suicidio"],
    "09-11": ["Día del Maestro Argentino", "Golpe de Estado en Chile (1973)", "Creación de la CTERA (1973)"],
    "09-12": ["Día de las Naciones Unidas para la Cooperación Sur-Sur"],
    "09-13": ["Día del Bibliotecario Argentino"],
    "09-15": ["Día Internacional de la Democracia"],
    "09-16": ["Día Internacional para la Preservación de la Capa de Ozono", "Día de los Derechos de los Estudiantes Secundarios"],
    "09-17": ["Día del Profesor Argentino"],
    "09-18": ["Desaparición de Jorge Julio López (2006)"],
    "09-19": ["Día del Preceptor / Preceptora"],
    "09-20": ["Día del Jubilado"],
    "09-21": ["Día Internacional de la Paz", "Día del Estudiante Argentino", "Inicio de la Primavera"],
    "09-23": [
        "Día Internacional de las Lenguas de Señas",
        "Promulgación de la Ley de Voto Femenino (1947)",
        "Día de las Bibliotecas Populares",
    ],
    "09-24": ["Batalla de Tucumán (1812)"],
    "09-26": ["Día del Empleado de Comercio"],
    "09-27": ["Día Mundial del Turismo", "Día del Derecho de los Niños a Jugar"],
    "09-28": [
        "Día Mundial contra la Rabia",
        "Día Internacional de Acceso Universal a la Información",
        "Día del Director de Escuela",
    ],
    "09-30": ["Día Internacional de la Traducción / Día del Traductor"],
    # ── OCTUBRE ────────────────────────────────────────────────────────────────
    "10-01": ["Día Internacional de las Personas Mayores", "Día del Vendedor"],
    "10-02": ["Día Internacional de la No Violencia"],
    "10-03": ["Día del Odontólogo"],
    "10-04": ["Día Mundial de los Animales"],
    "10-05": ["Día Mundial de los Docentes"],
    "10-08": ["Aniversario de la muerte del Che Guevara (1967)", "Día del Profesor de Educación Física"],
    "10-09": ["Día Mundial del Correo", "Día del Farmacéutico"],
    "10-10": ["Día Mundial de la Salud Mental", "Día del Panadero"],
    "10-11": ["Día Internacional de la Niña", "Último día de libertad de los Pueblos Originarios (1492)"],
    "10-12": ["Día del Respeto a la Diversidad Cultural (feriado nacional)"],
    "10-13": ["Día Internacional para la Reducción del Riesgo de Desastres", "Día del Psicólogo Argentino"],
    "10-15": ["Día Internacional de la Mujer Rural", "Día Mundial del Lavado de Manos", "Día de las Cooperadoras Escolares"],
    "10-16": ["Día Mundial de la Alimentación"],
    "10-17": ["Día Internacional para la Erradicación de la Pobreza", "Día de la Lealtad Peronista"],
    "10-18": ["Día Mundial de la Fotografía"],
    "10-20": ["Día de la Pediatría Argentina"],
    "10-22": ["Día Nacional del Derecho a la Identidad (Argentina)"],
    "10-24": ["Día de las Naciones Unidas", "Día del Diseñador Gráfico"],
    "10-25": ["Día de la Policía Federal Argentina"],
    "10-27": ["Día Mundial del Patrimonio Audiovisual"],
    "10-29": ["Aniversario de la Asignación Universal por Hijo (2009)"],
    "10-30": ["Día de la Restauración de la Democracia Argentina (1983)"],
    "10-31": ["Día Mundial de las Ciudades", "Halloween / Día de las Brujas"],
    # ── NOVIEMBRE ──────────────────────────────────────────────────────────────
    "11-01": ["Día de Todos los Santos"],
    "11-02": ["Día de los Fieles Difuntos / Día de los Muertos", "Día Internacional para Poner Fin a la Impunidad de Crímenes contra Periodistas"],
    "11-04": ["Marcha No al ALCA (2005)"],
    "11-05": ["Día Mundial de Concienciación sobre los Tsunamis"],
    "11-06": ["Día Internacional para Prevenir la Explotación del Medio Ambiente en la Guerra", "Día del Bancario / Empleado Bancario"],
    "11-07": ["Día del Periodista Deportivo"],
    "11-08": ["Día del Arquitecto Argentino"],
    "11-10": ["Día de la Tradición Argentina", "Día Mundial de la Ciencia para la Paz y el Desarrollo", "Día del Dibujante"],
    "11-11": ["Pacto de San José de Flores (1859)"],
    "11-13": ["Día del Pensamiento Nacional"],
    "11-14": ["Día Mundial de la Diabetes"],
    "11-15": ["Día de la Educación Técnica"],
    "11-16": ["Día Internacional para la Tolerancia", "Día del Deportista", "Fundación de la UNESCO (1945)"],
    "11-19": ["Día Mundial del Inodoro"],
    "11-20": ["Día de la Soberanía Nacional Argentina (feriado)", "Día Universal del Niño"],
    "11-21": ["Día Mundial de la Televisión"],
    "11-22": ["Día del Músico Argentino"],
    "11-24": ["Día del Trabajador Plástico"],
    "11-25": ["Día Internacional para la Eliminación de la Violencia contra la Mujer"],
    "11-26": ["Día del Químico"],
    "11-27": ["Día de la Educación de Jóvenes y Adultos"],
    "11-29": ["Día Internacional de Solidaridad con el Pueblo Palestino"],
    "11-30": ["Día del Librero (internacional)", "Día del Teatro"],
    # ── DICIEMBRE ──────────────────────────────────────────────────────────────
    "12-01": ["Día Mundial contra el SIDA"],
    "12-02": ["Día Internacional para la Abolición de la Esclavitud", "Día del Legislador"],
    "12-03": ["Día Internacional de las Personas con Discapacidad", "Día del Médico Argentino"],
    "12-04": ["Día de la Publicidad"],
    "12-05": ["Día Internacional del Voluntariado", "Día Mundial del Suelo", "Día de la Ama de Casa"],
    "12-07": ["Día Internacional de la Aviación Civil", "Día del Agente Bursátil"],
    "12-08": ["Día de la Inmaculada Concepción (feriado nacional)"],
    "12-09": ["Día Internacional de Conmemoración de las Víctimas de Genocidio", "Día Internacional contra la Corrupción"],
    "12-10": ["Día de los Derechos Humanos", "Día de la Democracia Argentina"],
    "12-11": ["Día Internacional de la Montaña"],
    "12-14": ["Sanción de la Ley Nacional de Educación (2006)"],
    "12-17": ["Día del Contador Público"],
    "12-18": ["Día Internacional del Migrante"],
    "12-19": ["Revuelta Popular argentina (2001)"],
    "12-20": ["Día Internacional de la Solidaridad Humana", "Día del Reportero Gráfico", "Revuelta Popular argentina (2001)"],
    "12-24": ["Nochebuena"],
    "12-25": ["Navidad"],
    "12-28": ["Día de los Inocentes (tradición latina)"],
    "12-31": ["Fin de Año / Nochevieja"],
}


def get_celebraciones(fecha: date) -> list[str]:
    """
    Devuelve la lista de celebraciones para una fecha dada, combinando
    el dict estático con las fechas de cálculo variable (Día de la Madre,
    Día del Padre, Carnavales, Viernes Santo).
    """
    resultado = list(CELEBRACIONES.get(fecha.strftime("%m-%d"), []))

    year = fecha.year
    pascua = _pascua(year)

    # Lunes y martes de Carnaval (feriados nacionales)
    miercoles_ceniza = pascua - timedelta(days=46)
    if fecha == miercoles_ceniza - timedelta(days=2):
        resultado.append("Lunes de Carnaval (feriado nacional)")
    elif fecha == miercoles_ceniza - timedelta(days=1):
        resultado.append("Martes de Carnaval (feriado nacional)")

    # Viernes Santo
    if fecha == pascua - timedelta(days=2):
        resultado.append("Viernes Santo (feriado nacional)")

    # Día de la Madre: 3er domingo de octubre (Argentina)
    if fecha == _nth_weekday(year, 10, 6, 3):
        resultado.append("Día de la Madre (Argentina)")

    # Día del Padre: 3er domingo de junio (Argentina)
    if fecha == _nth_weekday(year, 6, 6, 3):
        resultado.append("Día del Padre (Argentina)")

    return resultado


def get_mensaje_diade(fecha: date | None = None) -> str:
    """Devuelve el mensaje listo para el chat sobre las celebraciones del día."""
    if fecha is None:
        fecha = date.today()
    celebraciones = get_celebraciones(fecha)
    fecha_str = f"{fecha.day} de {_MESES[fecha.month]}"
    if not celebraciones:
        return f"Hoy, {fecha_str}, no hay ninguna celebración registrada."
    return f"Hoy, {fecha_str}: {' | '.join(celebraciones)}"
